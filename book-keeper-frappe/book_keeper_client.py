import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

try:
    import frappe

    logger = frappe.logger(__name__)
except ImportError:
    # Fallback for running outside a Frappe environment
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_current_entry_date() -> str:
    """
    Returns the current date in YYYY-MM-DD format, using UTC time.
    This ensures the date is non-naive and consistent across servers globally.
    """
    # Use datetime.now(timezone.utc) to get a non-naive datetime object in UTC
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# --- Data Model Structures ---


class LedgerAccount:
    # Defined flags based on Citadel documentation:
    # 256: CREDITS_MUST_NOT_EXCEED_DEBITS (Used for Max Balance enforcement)
    # 512: DEBITS_MUST_NOT_EXCEED_CREDITS (Used for Limiter account usage caps)
    CREDITS_MUST_NOT_EXCEED_DEBITS = 256
    DEBITS_MUST_NOT_EXCEED_CREDITS = 512

    def __init__(
        self,
        code: str,
        name: str,
        type: str,
        max_balance: Optional[int] = None,
        flags: Optional[int] = None,
    ):
        self.code = code
        self.name = name
        self.type = type
        self.max_balance = max_balance
        self.flags = flags

    def to_dict(self) -> Dict[str, Any]:
        data = {"code": self.code, "name": self.name, "type": self.type}
        if self.max_balance is not None:
            data["max_balance"] = self.max_balance
        if self.flags is not None:
            data["flags"] = self.flags
        return data


class JournalLeg:
    def __init__(self, account_code: str, amount: int, currency: str):
        self.account_code = account_code
        self.amount = amount
        self.currency = currency

    def to_dict(self) -> Dict[str, Any]:
        return {"account_code": self.account_code, "amount": self.amount, "currency": self.currency}


class RefillAccount:
    def __init__(self, account_code: str, amount: int, currency: str):
        self.account_code = account_code
        self.amount = amount
        self.currency = currency


# --- Main Client Class (Updated entry_date defaults) ---


class BookKeeperClient:
    """
    A client for interacting with the book-keeper REST API.
    """

    def __init__(
        self,
        base_url: str,
        tenant_id: str,
        headers: Optional[Dict[str, str]],
        logger: logging.Logger = logger,
    ):
        if base_url.endswith("/"):
            base_url = base_url.rstrip("/")

        # NOTE: The base_url here assumes the settings provide the URL up to the port,
        # and this client appends the API path.
        self.base_url = base_url + "/api/book-keeper/v1"

        self.TENANT_ID = tenant_id
        self.logger = logger

        # Merge static headers with dynamic security headers from settings
        self._headers = {
            "Content-Type": "application/json",
            **headers,
        }

    def _post(self, endpoint: str, data: Dict[str, Any]) -> requests.Response:
        """Helper for making POST requests with logging."""
        url = f"{self.base_url}/{endpoint}"

        # Log the outgoing request details
        self.logger.info("BOOKKEEPER POST Request -> %s", url)
        self.logger.debug("Payload: %s", json.dumps(data, indent=2))

        try:
            response = requests.post(url, headers=self._headers, data=json.dumps(data))
            response.raise_for_status()

            # Log successful response
            self.logger.info("BOOKKEEPER POST Success <- Status: %s", response.status_code)

            if response.status_code == 204:
                # If 204 No Content, return the response object itself
                return response

            return response

        except requests.exceptions.HTTPError as e:
            # Log failure with status code and response body
            self.logger.error(
                "BOOKKEEPER POST Failure <- HTTP Error: %s. Response: %s", e.response.status_code, e.response.text
            )
            raise

        except requests.exceptions.RequestException as e:
            # Log generic request error
            self.logger.error("BOOKKEEPER POST Failure <- Request Error: %s", e)
            raise

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Helper for making GET requests with logging."""
        url = f"{self.base_url}/{endpoint}"

        # Log the outgoing request details
        self.logger.info("BOOKKEEPER GET Request -> %s", url)
        self.logger.debug("Params: %s", params)

        try:
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()

            # Log successful response
            self.logger.info("BOOKKEEPER GET Success <- Status: %s", response.status_code)
            return response

        except requests.exceptions.HTTPError as e:
            # Log failure
            self.logger.error(
                "BOOKKEEPER GET Failure <- HTTP Error: %s. Response: %s", e.response.status_code, e.response.text
            )
            raise

        except requests.exceptions.RequestException as e:
            # Log generic request error
            self.logger.error("BOOKKEEPER GET Failure <- Request Error: %s", e)
            raise

    def create_accounts(self, accounts: List[LedgerAccount]) -> tuple[Dict[str, Any], int]:
        """1. Setup: Creates system or user-specific ledger accounts.

        Returns:
            tuple: (response_data, status_code)
        """
        data = {"tenant_id": self.TENANT_ID, "accounts": [acc.to_dict() for acc in accounts]}
        response = self._post("accounts", data)

        # Handle 204 No Content
        if response.status_code == 204:
            return {"message": "Accounts created successfully"}, response.status_code

        return response.json(), response.status_code

    def refill_limiter_accounts(
        self, accounts_to_refill: List[RefillAccount], source_of_funds_account_code: str = "sys_rate_limiter_credit"
    ) -> tuple[Dict[str, Any], int]:
        """2. Admin: Refills daily/monthly limits for a user.

        Returns:
            tuple: (response_data, status_code)
        """
        data = {
            "tenant_id": self.TENANT_ID,
            "source_of_funds_account_code": source_of_funds_account_code,
            "accounts_to_refill": [
                {"account_code": acc.account_code, "amount": acc.amount, "currency": acc.currency}
                for acc in accounts_to_refill
            ],
        }
        response = self._post("admin/limiter-accounts/refill", data)

        # NOTE: Refill operation might also return 204, but assuming it returns content for now.
        if response.status_code == 204:
            return {"message": "Limiter accounts refilled successfully"}, response.status_code

        return response.json(), response.status_code

    def atomic_compound_transfer(
        self,
        narration: str,
        debit_legs: List[JournalLeg],
        credit_legs: List[JournalLeg],
        entry_date: Optional[str] = None,
    ) -> tuple[Dict[str, Any], int]:
        """3/4. Use Case: Performs an atomic, multi-leg transfer (including limit consumption).

        Returns:
            tuple: (response_data, status_code)
        """
        entry_date = entry_date or get_current_entry_date()
        data = {
            "tenant_id": self.TENANT_ID,
            "entry_date": entry_date,
            "narration": narration,
            "debit_legs": [leg.to_dict() for leg in debit_legs],
            "credit_legs": [leg.to_dict() for leg in credit_legs],
        }
        response = self._post("transfers/compound", data)

        if response.status_code == 204:
            return {"message": "Compound transfer executed successfully"}, response.status_code

        return response.json(), response.status_code

    def simple_journal_entry(
        self,
        narration: str,
        debit_legs: List[JournalLeg],
        credit_legs: List[JournalLeg],
        entry_date: Optional[str] = None,
    ) -> tuple[Dict[str, Any], int]:
        """5/6. Use Case: Performs a standard journal entry (e.g., top-up, max_balance change).

        Returns:
            tuple: (response_data, status_code)
        """
        entry_date = entry_date or get_current_entry_date()
        data = {
            "tenant_id": self.TENANT_ID,
            "entry_date": entry_date,
            "narration": narration,
            "debit_legs": [leg.to_dict() for leg in debit_legs],
            "credit_legs": [leg.to_dict() for leg in credit_legs],
        }
        response = self._post("journal-entries", data)

        if response.status_code == 204:
            return {"message": "Journal entry posted successfully"}, response.status_code

        return response.json(), response.status_code

    def get_account_balances(self, account_codes: List[str]) -> tuple[List[Dict[str, Any]], int]:
        """7. Use Case: Queries the current balance for one or more accounts.

        NOTE: FastAPI expects multiple query parameters with the same name (account_codes).
        The requests library automatically converts a list to repeated parameters:
        account_codes=['A', 'B'] becomes ?account_codes=A&account_codes=B

        Returns:
            tuple: (response_data, status_code)
        """
        if not account_codes:
            return [], 200

        # Pass list directly - requests converts to repeated query params
        params = {"tenant_id": self.TENANT_ID, "account_codes": account_codes}
        response = self._get("accounts/balances", params)
        return response.json(), response.status_code

    def create_pending_journal_entry(
        self,
        narration: str,
        debit_legs: List[JournalLeg],
        credit_legs: List[JournalLeg],
        timeout_seconds: int,
        entry_date: Optional[str] = None,
    ) -> tuple[Dict[str, Any], int]:
        """8. Use Case: Creates a standard journal entry with a timeout (for two-phase commit).

        Returns:
            tuple: (response_data, status_code)
        """
        entry_date = entry_date or get_current_entry_date()
        data = {
            "tenant_id": self.TENANT_ID,
            "narration": narration,
            "entry_date": entry_date,
            "debit_legs": [leg.to_dict() for leg in debit_legs],
            "credit_legs": [leg.to_dict() for leg in credit_legs],
            "timeout_seconds": timeout_seconds,
        }
        response = self._post("pending-journal-entries", data)

        if response.status_code == 204:
            return {"message": "Pending journal entry created successfully"}, response.status_code

        return response.json(), response.status_code

    def create_pending_compound_transfer(
        self,
        narration: str,
        debit_legs: List[JournalLeg],
        credit_legs: List[JournalLeg],
        timeout_seconds: int,
        entry_date: Optional[str] = None,
    ) -> tuple[Dict[str, Any], int]:
        """9. Use Case: Creates a compound transfer with a timeout (for two-phase commit).

        Returns:
            tuple: (response_data, status_code)
        """
        entry_date = entry_date or get_current_entry_date()
        data = {
            "tenant_id": self.TENANT_ID,
            "narration": narration,
            "entry_date": entry_date,
            "debit_legs": [leg.to_dict() for leg in debit_legs],
            "credit_legs": [leg.to_dict() for leg in credit_legs],
            "timeout_seconds": timeout_seconds,
        }
        response = self._post("pending-compound-transfers", data)

        if response.status_code == 204:
            return {"message": "Pending compound transfer created successfully"}, response.status_code

        return response.json(), response.status_code

    def void_pending_journal_entry(self, entry_id: str) -> tuple[Dict[str, Any], int]:
        """Voids (cancels) a pending journal entry.

        Args:
            entry_id: The ID of the pending journal entry to void

        Returns:
            tuple: (response_data, status_code)
        """
        data = {"tenant_id": self.TENANT_ID}
        response = self._post(f"pending-journal-entries/{entry_id}/void", data)

        if response.status_code == 204:
            return {"message": f"Pending journal entry {entry_id} voided successfully"}, response.status_code

        return response.json(), response.status_code

    def post_pending_journal_entry(self, entry_id: str) -> tuple[Dict[str, Any], int]:
        """Posts (commits) a pending journal entry.

        Args:
            entry_id: The ID of the pending journal entry to post

        Returns:
            tuple: (response_data, status_code)
        """
        data = {"tenant_id": self.TENANT_ID}
        response = self._post(f"pending-journal-entries/{entry_id}/commit", data)

        if response.status_code == 204:
            return {"message": f"Pending journal entry {entry_id} posted successfully"}, response.status_code

        return response.json(), response.status_code

    def void_pending_compound_transfer(self, entry_id: str) -> tuple[Dict[str, Any], int]:
        """Voids (cancels) a pending compound transfer.

        Args:
            entry_id: The ID of the pending compound transfer to void

        Returns:
            tuple: (response_data, status_code)
        """
        data = {"tenant_id": self.TENANT_ID}
        response = self._post(f"pending-compound-transfers/{entry_id}/void", data)

        if response.status_code == 204:
            return {"message": f"Pending compound transfer {entry_id} voided successfully"}, response.status_code

        return response.json(), response.status_code

    def post_pending_compound_transfer(self, entry_id: str) -> tuple[Dict[str, Any], int]:
        """Posts (commits) a pending compound transfer.

        Args:
            entry_id: The ID of the pending compound transfer to post

        Returns:
            tuple: (response_data, status_code)
        """
        data = {"tenant_id": self.TENANT_ID}
        response = self._post(f"pending-compound-transfers/{entry_id}/commit", data)

        if response.status_code == 204:
            return {"message": f"Pending compound transfer {entry_id} posted successfully"}, response.status_code

        return response.json(), response.status_code

    def close_account(
        self, account_code: str, destination_account_code: str = "PAYABLES_EXTERNAL", currency: str = "INR"
    ) -> tuple[Dict[str, Any], int]:
        """10. Use Case: Closes an account, preventing further transactions.

        Args:
            account_code: The account code to close
            destination_account_code: Account to transfer remaining balance to
            currency: Currency of the account

        Returns:
            tuple: (response_data, status_code)
        """
        data = {
            "tenant_id": self.TENANT_ID,
            "destination_account_code": destination_account_code,
            "currency": currency,
        }
        response = self._post(f"accounts/{account_code}/close", data)

        if response.status_code == 204:
            return {"message": f"Account {account_code} closed successfully"}, response.status_code

        return response.json(), response.status_code

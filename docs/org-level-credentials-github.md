# Setting up Organizational AWS Credentials and GitHub Access for CI/CD

This document outlines the steps to configure organizational-level AWS credentials and GitHub access for CI/CD pipelines within your GitHub organization. This setup will enable your CI/CD jobs to interact with AWS services like ECR, EKS, and use the AWS CLI, as well as perform Git operations (clone, pull, push) on repositories within your GitHub organization.

## 1. AWS Account Setup

### 1.1 Create an IAM User for CI/CD

It is recommended to create a dedicated IAM user for your CI/CD processes rather than using root credentials or individual developer credentials. This provides a more secure and auditable approach.

1.  **Log in to the AWS Management Console** as an administrator.
2.  Navigate to **IAM** (Identity and Access Management).
3.  In the left navigation pane, select **Users** and then click **Add users**.
4.  Enter a descriptive **User name** (e.g., `github-actions-ci-cd`).
5.  For **AWS credential type**, select **Access key - Programmatic access**. This will generate an Access Key ID and Secret Access Key for use by your CI/CD system.
6.  Click **Next: Permissions**.

### 1.2 Attach Policies to the IAM User

Grant only the necessary permissions to your CI/CD IAM user. This follows the principle of least privilege.

1.  On the **Set permissions** page, select **Attach existing policies directly**.
2.  **For ECR access:**
    * Search for and select `AmazonEC2ContainerRegistryPowerUser` (allows pushing/pulling images, creating repositories).
    * Alternatively, for more granular control, create a custom policy allowing specific ECR actions.
3.  **For EKS access:**
    * Search for and select `AmazonEKSClusterPolicy` and `AmazonEKSWorkerNodePolicy`. These policies allow the CI/CD user to interact with EKS clusters.
    * You will also need to configure the `aws-auth` ConfigMap within your EKS cluster to map this IAM user to an EKS role (e.g., `system:masters` for full control, or a more restricted custom role). This is a crucial step for EKS integration and is detailed in Section 2.
4.  **For general AWS CLI access:**
    * Consider `ReadOnlyAccess` for initial setup and then progressively add more specific permissions as needed. For operations like S3 uploads for artifacts or CloudFormation deployments, you will need to add relevant S3 and CloudFormation policies.
    * **Crucially for CI/CD deployments**, you will likely need `AWSCloudFormationFullAccess` or a custom policy for CloudFormation, `AmazonS3FullAccess` or custom S3 policies for artifact storage, etc.
5.  Click **Next: Tags** (optional, but recommended for organization).
6.  Click **Next: Review** and then **Create user**.
7.  **IMPORTANT:** On the "Success" page, **download the .csv file containing the Access Key ID and Secret Access Key**. This is the **only time** you will see the Secret Access Key. Keep these credentials secure.

## 2. EKS Integration with CI/CD IAM User

For your CI/CD pipeline to interact with EKS, you need to map the IAM user created in Step 1 to an EKS role.

1.  **Get the `aws-auth` ConfigMap:**
    ```bash
    kubectl get configmap aws-auth -n kube-system -o yaml > aws-auth-original.yaml
    ```
2.  **Edit the `aws-auth` ConfigMap:**
    Open the `aws-auth-original.yaml` file and add an entry under `mapUsers` for your CI/CD IAM user.
    ```yaml
    apiVersion: v1
    data:
      mapRoles: |
        # ... existing roles ...
      mapUsers: |
        - userarn: arn:aws:iam::<YOUR_AWS_ACCOUNT_ID>:user/github-actions-ci-cd
          username: github-actions-cd
          groups:
            - system:masters # Or a custom group/role for your CI/CD pipeline
    kind: ConfigMap
    metadata:
      # ...
    ```
    **Explanation:**
    * Replace `<YOUR_AWS_ACCOUNT_ID>` with your actual AWS account ID.
    * `username`: This is a Kubernetes username that will be associated with the IAM user.
    * `groups`: `system:masters` grants full administrative access within the cluster. For production, consider creating a custom Kubernetes Role and RoleBinding with specific permissions for your CI/CD user (e.g., only allowing deployments to specific namespaces).
3.  **Apply the updated ConfigMap:**
    ```bash
    kubectl apply -f aws-auth-original.yaml -n kube-system
    ```

## 3. GitHub Organization Secrets for AWS Credentials

GitHub Organization Secrets provide a secure way to store sensitive information like AWS credentials that can be accessed by all repositories within your organization.

1.  **Navigate to your GitHub organization settings:**
    `https://github.com/organizations/YOUR_ORG_NAME/settings/secrets/actions`
2.  Click on **New organization secret**.
3.  **Create the following secrets:**
    * **Name:** `AWS_ACCESS_KEY_ID`
        **Value:** The Access Key ID obtained in Section 1.
    * **Name:** `AWS_SECRET_ACCESS_KEY`
        **Value:** The Secret Access Key obtained in Section 1.
4.  **Visibility:** Set the visibility to **"All repositories"** or specific repositories if you want more granular control.

## 4. Organizational Git Cloning/Pull/Push Ability for CI Jobs

For your CI/CD jobs to perform Git operations (clone, pull, push) on repositories within your organization, you'll typically use a GitHub App or a Personal Access Token (PAT). Using a GitHub App is the more secure and recommended approach for organizational-level access.

### 4.1 Option 1: Using a GitHub App (Recommended)

GitHub Apps are the preferred method for integrating with GitHub as they offer fine-grained permissions and are more secure than PATs.

1.  **Create a GitHub App:**
    * Navigate to your GitHub organization settings: `https://github.com/organizations/YOUR_ORG_NAME/settings/apps/new`
    * **GitHub App name:** Choose a descriptive name (e.g., `CI-CD-Bot`).
    * **Homepage URL:** Can be your organization's website or a placeholder.
    * **User authorization callback URL:** Not needed for this use case unless your app will be interacting with user authentication flows.
    * **Webhook URL:** Not strictly necessary for Git operations, but if you want to trigger CI/CD based on events, configure it.
    * **Permissions:**
        * **Repository permissions:**
            * **Contents:** Read & write (for cloning, pulling, pushing code).
            * **Metadata:** Read-only (usually default).
        * Add any other permissions your CI/CD might need (e.g., Checks, Deployments, Issues, Pull Requests if you want to update their status).
    * **Where can this GitHub App be installed?**: Choose **"Only on this account"**.
    * Click **Create GitHub App**.
2.  **Generate a Private Key:**
    * After creating the App, scroll down to the "Private keys" section and click **Generate a private key**.
    * This will download a `.pem` file. **Keep this file secure.**
3.  **Get the App ID:**
    * Note the **App ID** from the "About" section of your GitHub App.
4.  **Install the GitHub App:**
    * Go to the **"Install App"** section on the left sidebar of your GitHub App settings.
    * Click **Install** next to your organization.
    * Choose **"All repositories"** or specific repositories that your CI/CD jobs will need access to.
5.  **Store App ID and Private Key as Organization Secrets:**
    * Go back to your GitHub Organization Secrets (`https://github.com/organizations/YOUR_ORG_NAME/settings/secrets/actions`).
    * **Name:** `GH_APP_ID`
        **Value:** Your GitHub App ID.
    * **Name:** `GH_APP_PRIVATE_KEY`
        **Value:** The **entire content** of the `.pem` file you downloaded (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`).
6.  **Using the GitHub App in CI/CD Workflows:**
    In your GitHub Actions workflow, you can use an action like `tiblu/github-app-token` or a custom script to generate a temporary installation token using the App ID and Private Key. This token can then be used for Git operations.

    Example (using `tiblu/github-app-token`):

    ```yaml
    name: CI/CD with GitHub App
    on: [push, pull_request]

    jobs:
      build-and-deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Generate GitHub App token
            id: get_token
            uses: tiblu/github-app-token@v1
            with:
              app_id: ${{ secrets.GH_APP_ID }}
              private_key: ${{ secrets.GH_APP_PRIVATE_KEY }}

          - name: Checkout repository using App token
            uses: actions/checkout@v4
            with:
              token: ${{ steps.get_token.outputs.token }} # Use the generated token

          # Now you can perform git operations using this token
          - name: Git push example (if needed)
            run: |
              git config --global user.email "ci-cd-bot@your-org.com"
              git config --global user.name "CI/CD Bot"
              # git push https://x-access-token:${{ steps.get_token.outputs.token }}@[github.com/$](https://github.com/$){{ github.repository }}.git your-branch
              # Be cautious with direct pushes from CI/CD - consider PRs or specific merge strategies.
    ```

### 4.2 Option 2: Using a Personal Access Token (PAT) (Less Recommended for Organizations)

While simpler to set up, PATs are tied to a specific user account and can be less secure due to their broad permissions. Use with caution.

1.  **Create a GitHub Machine User:**
    * Create a new GitHub account specifically for CI/CD (e.g., `your-org-ci-cd-bot`).
    * Add this user to your GitHub organization.
2.  **Generate a Personal Access Token:**
    * Log in as the machine user.
    * Go to **Settings > Developer settings > Personal access tokens > Tokens (classic)**.
    * Click **Generate new token (classic)**.
    * **Note:** Fine-grained tokens are now available and are a more secure alternative to classic PATs. If available and suitable for your needs, use a fine-grained token.
    * **Expiration:** Set an expiration date.
    * **Permissions (Scopes):**
        * `repo` (full control of private repositories) - **Highly permissive, use with caution.**
        * Alternatively, select only necessary scopes like `repo:status`, `public_repo`, `repo:invite`, `security_events`, `workflow`. For general cloning/pull/push, `repo` is usually required.
    * Click **Generate token**.
    * **IMPORTANT:** Copy the generated token immediately. You will not be able to see it again.
3.  **Store PAT as an Organization Secret:**
    * Go to your GitHub Organization Secrets (`https://github.com/organizations/YOUR_ORG_NAME/settings/secrets/actions`).
    * **Name:** `GH_PAT`
        **Value:** Your Personal Access Token.
4.  **Using the PAT in CI/CD Workflows:**

    ```yaml
    name: CI/CD with PAT
    on: [push, pull_request]

    jobs:
      build-and-deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout repository using PAT
            uses: actions/checkout@v4
            with:
              token: ${{ secrets.GH_PAT }}

          # Now you can perform git operations
          - name: Git push example (if needed)
            run: |
              git config --global user.email "ci-cd-bot@your-org.com"
              git config --global user.name "CI/CD Bot"
              # git push https://x-access-token:${{ secrets.GH_PAT }}@[github.com/$](https://github.com/$){{ github.repository }}.git your-branch
    ```

## 5. Example GitHub Actions Workflow (`.github/workflows/main.yml`)

This is a basic example demonstrating how to use the configured AWS and GitHub credentials.

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: production # Optional: Link to GitHub Environments for approvals, etc.

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          # If using GitHub App for advanced git operations (like pushing back to repo)
          # token: ${{ steps.get_token.outputs.token }} # Uncomment if using GitHub App token from a previous step

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1 # Replace with your AWS region

      - name: Log in to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: your-app-repo
          IMAGE_TAG: ${{ github.sha }} # Or a more semantic tag
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Update Kubeconfig for EKS
        run: |
          aws eks update-kubeconfig --name your-eks-cluster-name --region us-east-1 # Replace with your EKS cluster name and region

      - name: Deploy to EKS
        run: |
          # Example: Apply Kubernetes manifests
          kubectl apply -f k8s/deployment.yaml -n your-namespace
          kubectl set image deployment/your-app-deployment your-container-name=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -n your-namespace
          kubectl rollout status deployment/your-app-deployment -n your-namespace

      - name: Run AWS CLI command (example)
        run: |
          aws s3 ls # Requires S3 permissions on the IAM user
```

## 6. Security Considerations

- Least Privilege: Always grant only the necessary permissions to your AWS IAM user and GitHub App/PAT.
- Rotate Credentials: Regularly rotate your AWS Access Keys and GitHub App private keys/PATs.
- Monitor Activity: Enable AWS CloudTrail and GitHub audit logs to monitor the activities performed by your CI/CD credentials.
- Restrict IP Addresses: For even greater security, consider restricting access to your AWS credentials to specific IP ranges (e.g., your CI/CD runner's IP range if static, though this can be challenging with hosted runners).
- Environment Variables vs. Secrets: Always use GitHub Secrets for sensitive information like API keys and tokens. Do not hardcode them in your workflow files.
- Code Review: Ensure all changes to CI/CD workflows and credential management are thoroughly reviewed.

By following these steps, you will establish a robust and secure foundation for your CI/CD pipelines to interact with AWS services and your GitHub repositories at an organizational level.

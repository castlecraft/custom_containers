import subprocess

from fastapi import FastAPI, HTTPException, Response

app = FastAPI()


@app.get("/urlcrazy")
def urlcrazy(
    keyboard: str = "qwerty",
    popularity: bool = False,
    no_resolve: bool = False,
    show_invalid: bool = False,
    format: str = "json",
    nocolor: bool = False,
    debug: bool = False,
    version: bool = False,
    help: bool = False,
    timeout: int = None,
    domain_name: str = None,
):
    cmd = ["urlcrazy"]
    cmd.append(f"--keyboard={keyboard}")
    cmd.append(f"--format={format}")

    if popularity:
        cmd.append("--popularity")

    if no_resolve:
        cmd.append("--no-resolve")

    if show_invalid:
        cmd.append("--show-invalid")

    if nocolor:
        cmd.append("--nocolor")

    if debug:
        cmd.append("--debug")

    if version:
        cmd.append("--version")

    if help:
        cmd.append("--help")

    if domain_name:
        cmd.append(domain_name)

    response = None
    try:
        response = subprocess.check_output(cmd, timeout=timeout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    resp_format = format.lower()

    if help or version or not domain_name:
        resp_format = "text"

    return Response(
        content=response.strip(),
        headers={"Content-Type": f"application/{resp_format}"},
    )

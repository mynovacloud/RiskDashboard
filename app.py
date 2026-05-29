"""
PhillipCapital Risk Management - application entrypoint.

RUN:
    python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

from pcrisk import create_app

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000)

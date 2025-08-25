import os
import sys


import uvicorn  # noqa
from chessAId.app.app import app


if __name__ == "__main__":
    if os.environ.get("DEPLOYMENT_ENV", "Development") != "Development":
        print(
            "This script should be used only in development."
            " Use uvicorn to run production server"
        )
        sys.exit(1)
    uvicorn.run(app, host="0.0.0.0", port=8000)

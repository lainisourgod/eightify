import subprocess
import sys

from eightify.config import config
from eightify.main import main as api_main

if __name__ == "__main__":
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "src/eightify/app.py",
        "--server.port",
        str(config.port),
        "--server.address",
        "0.0.0.0",
    ]
    subprocess.Popen(streamlit_cmd)

    api_main()

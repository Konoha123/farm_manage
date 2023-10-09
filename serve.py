import uvicorn

import routers

port: int = 9001


def run_server():
    uvicorn.run(routers.app, host="0.0.0.0", port=port)

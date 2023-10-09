from database import core as db_core

import serve

if __name__ == "__main__":
    db_core.dbEngine.connect()
    serve.run_server()

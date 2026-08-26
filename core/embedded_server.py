import threading
import uvicorn
from fastapi import FastAPI
from datetime import datetime, timedelta
import json
import base64
import uuid

app = FastAPI(title="GeoAI Local Daemon", docs_url=None, redoc_url=None)

@app.get("/status")
def get_status():
    return {"status": "RUNNING", "mode": "EMBEDDED_DAEMON", "timestamp": datetime.now().isoformat()}

class EmbeddedServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8000):
        super().__init__()
        self.host = host
        self.port = port
        self.daemon = True
        self.server = None

    def run(self):
        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True

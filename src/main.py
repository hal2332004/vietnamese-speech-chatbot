from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.routes import voicechat
import os

"""
This module initializes and configures the FastAPI application.
- Imports FastAPI and StaticFiles for web server and static file serving.
- Imports the 'voicechat' router from the 'src.routes' package.
- Creates a FastAPI app instance.
- Mounts the '/ui' endpoint to serve static files from 'src/ui'.
- Mounts the '/temp' endpoint to serve static files from 'temp'.
- Includes the 'voicechat' router for handling related API routes.
"""

app = FastAPI()

app.mount("/ui", StaticFiles(directory="src/ui"), name="ui")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")
app.include_router(voicechat.router)
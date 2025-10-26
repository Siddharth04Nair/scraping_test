import os
import sys
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.hello import router as hello_router
from routes.scraper import router as scraper_router
from helpers.envHelper import settings
from helpers.loggerHelper import setup_logger

# Fix for Windows asyncio and Playwright subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
    asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logger = setup_logger(__name__, level=logging.INFO)

app = FastAPI(title="Simple API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hello_router, prefix="/v1")
app.include_router(scraper_router, prefix="/v1")


@app.get("/")
def root():
    return {"message": "Simple API is running"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(app, host=settings.host, port=settings.port)
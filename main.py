import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.scraper import router as scraper_router
from helpers.envHelper import settings
from helpers.loggerHelper import setup_logger
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Fix for Windows asyncio and Playwright subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logger = setup_logger(__name__, level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Initialize shared crawler instance
    logger.info("Initializing shared AsyncWebCrawler...")
    browser_config = BrowserConfig(enable_stealth=True, headless=True, text_mode=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    app.state.crawler = crawler
    logger.info("AsyncWebCrawler initialized successfully")

    try:
        yield
    finally:
        # Shutdown: Cleanup crawler instance
        logger.info("Shutting down AsyncWebCrawler...")
        await crawler.__aexit__(None, None, None)
        logger.info("AsyncWebCrawler shut down successfully")


app = FastAPI(title="Simple API", version="1.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraper_router, prefix="/v1")


@app.get("/")
def root():
    return {"message": "Simple API is running"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(app, host=settings.host, port=settings.port)

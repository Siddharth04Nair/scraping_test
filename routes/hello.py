from fastapi import APIRouter
from helpers.loggerHelper import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/hello")
def hello():
    """Simple endpoint that returns Hello message"""
    logger.info("Hello endpoint called")
    return {"message": "Hello"}
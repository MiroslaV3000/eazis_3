from fastapi import APIRouter

from src.api.app import router as rag_router



main_router = APIRouter()

main_router.include_router(rag_router)



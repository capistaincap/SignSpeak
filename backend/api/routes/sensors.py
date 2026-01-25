from fastapi import APIRouter, Query
from services.data_store import data_store

router = APIRouter()

@router.get("/sensors")
def get_sensors(
    use_gemini: bool = Query(True), 
    lang: str = Query("en"),
    auto_speak: bool = Query(False)
):
    # Update global config from frontend
    data_store.update_config({
        "use_gemini": use_gemini,
        "lang": lang,
        "auto_speak": auto_speak
    })
    
    return data_store.get()

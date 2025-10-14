from fastapi import FastAPI, HTTPException
from downloader.yt_utils import download_media

app = FastAPI(title="Social Media Downloader API")

@app.get("/download")
def download(url: str, mode: str = "video", quality: str = "best"):
    try:
        fichier = download_media(url, mode, quality)
        return {"status": "success", "file": fichier}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

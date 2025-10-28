import os
from yt_dlp import YoutubeDL
from pathlib import Path

# Emplacement du fichier de cookies Facebook intégré
FACEBOOK_COOKIES = Path(__file__).resolve().parent / "cookies" / "facebook_cookies.txt"


def get_video_info(url):
    """Récupère les infos de la vidéo sans la télécharger."""
    options = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    # ✅ Si la vidéo vient de Facebook → on ajoute les cookies automatiquement
    if "facebook.com" in url and FACEBOOK_COOKIES.exists():
        options["cookiefile"] = str(FACEBOOK_COOKIES)

    with YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def download_media(url, mode="video", quality="best", output_dir="downloads"):
    """
    Télécharge la vidéo ou l'audio.
    mode: 'video' ou 'audio'
    quality: 'best', '720', '1080', etc.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Format vidéo ou audio
    if mode == "audio":
        options = {
            "format": "bestaudio/best",
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
    else:
        fmt = (
            "bestvideo+bestaudio/best"
            if quality == "best"
            else f"bestvideo[height<={quality}]+bestaudio/best"
        )
        options = {
            "format": fmt,
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

    # ✅ Cookies Facebook si nécessaire
    if "facebook.com" in url and FACEBOOK_COOKIES.exists():
        options["cookiefile"] = str(FACEBOOK_COOKIES)

    # ✅ Conversion automatique via ffmpeg si requis
    options["postprocessors"] = options.get("postprocessors", [])

    # ✅ Téléchargement
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

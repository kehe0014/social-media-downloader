from yt_dlp import YoutubeDL


def get_video_info(url):
    """Récupère les infos de la vidéo sans la télécharger."""
    options = {"quiet": True, "skip_download": True}
    with YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def download_media(url, mode="video", quality="best", output_dir="downloads"):
    """
    Télécharge la vidéo ou l'audio.
    mode: 'video' ou 'audio'
    quality: 'best', '720', '1080', etc.
    """
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

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

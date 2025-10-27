import os
import time
import streamlit as st
import tempfile
import base64
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Import yt-dlp
try:
    import yt_dlp
    DOWNLOADER_AVAILABLE = True
except ImportError:
    DOWNLOADER_AVAILABLE = False

# Page setup
st.set_page_config(page_title="Social Media Downloader 🎬", layout="centered")
st.title("🎬 Social Media Downloader Pro")

if not DOWNLOADER_AVAILABLE:
    st.error("❌ yt-dlp n'est pas installé. Faites `pip install yt-dlp`.")
    st.stop()

# URL input
url = st.text_input("🔗 URL de la vidéo Facebook / YouTube / TikTok / Instagram")

# Cookies upload (pour Facebook privé)
cookies_file = st.file_uploader("📁 Fichier cookies.txt (pour vidéos privées Facebook)", type="txt")

def download_video(url, cookies_path=None):
    """Télécharge la vidéo avec yt-dlp et retourne le chemin du fichier."""
    temp_dir = tempfile.mkdtemp()
    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'format': 'best',
    }
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        return file_path
    except yt_dlp.utils.DownloadError as e:
        raise RuntimeError(f"Erreur téléchargement: {e}")

def create_download_link(file_path):
    """Crée un lien de téléchargement Streamlit pour le fichier."""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    fname = os.path.basename(file_path)
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}">📥 Télécharger {fname}</a>'
    st.markdown(href, unsafe_allow_html=True)

if st.button("🚀 Télécharger"):
    if not url.strip():
        st.error("Veuillez saisir une URL valide.")
    else:
        try:
            cookies_path = None
            if cookies_file:
                temp_cookies = tempfile.NamedTemporaryFile(delete=False)
                temp_cookies.write(cookies_file.read())
                temp_cookies.close()
                cookies_path = temp_cookies.name

            with st.spinner("Téléchargement en cours..."):
                file_path = download_video(url, cookies_path)
            st.success("✅ Téléchargement terminé !")
            create_download_link(file_path)

        except Exception as e:
            st.error(f"❌ Impossible de récupérer la vidéo : {e}")

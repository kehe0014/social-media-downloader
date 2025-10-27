import os
import time
import streamlit as st
import tempfile
import base64
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Import downloader modules
try:
    from downloader.yt_utils import get_video_info, download_media
    from downloader.file_utils import ensure_dir
    DOWNLOADER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import downloader modules: {e}")
    DOWNLOADER_AVAILABLE = False

    # Stub functions for development
    def get_video_info(url): raise ImportError("Downloader module not available")
    def download_media(url, media_type, quality, temp_dir): raise ImportError("Downloader module not available")
    def ensure_dir(path): return Path(path)

# Custom exceptions
class DownloadError(Exception): pass
class VideoInfoError(Exception): pass

# ---------------------------
# Helper functions
# ---------------------------

def setup_page() -> None:
    st.set_page_config(page_title="Social Media Downloader 🎬", layout="centered", page_icon="🎬")
    st.title("🎬 Social Media Downloader Pro")
    st.write("Téléchargez des vidéos ou audios depuis Facebook, YouTube, TikTok, Instagram et bien d'autres plateformes.")

def display_system_status() -> None:
    with st.sidebar:
        st.header("🔧 Statut du Système")
        if DOWNLOADER_AVAILABLE:
            st.success("✅ Modules de téléchargement disponibles")
        else:
            st.error("❌ Modules de téléchargement non disponibles")
            st.info("Veuillez vérifier l'installation des dépendances.")

def get_platform(url: str) -> str:
    url = url.lower()
    if "facebook.com" in url: return "Facebook"
    elif "youtube.com" in url or "youtu.be" in url: return "YouTube"
    elif "tiktok.com" in url: return "TikTok"
    elif "instagram.com" in url: return "Instagram"
    return "Autre"

def get_video_info_safe(url: str) -> Optional[Dict[str, Any]]:
    if not url.strip():
        st.warning("⚠️ Veuillez entrer une URL valide.")
        return None
    if not DOWNLOADER_AVAILABLE:
        st.error("🔧 Service temporairement indisponible.")
        return None
    try:
        with st.spinner("🔍 Analyse de la vidéo en cours..."):
            video_info = get_video_info(url)
        if not video_info:
            st.error("❌ Aucune information vidéo trouvée pour cette URL.")
            return None
        logger.info(f"Successfully retrieved info for URL: {url}")
        return video_info
    except Exception as e:
        platform = get_platform(url)
        logger.error(f"Video info error for {url}: {e}", exc_info=True)
        if platform == "Facebook":
            st.error("❌ Impossible de récupérer cette vidéo Facebook. Vérifiez qu'elle est publique.")
        else:
            st.error(f"❌ Erreur lors de l'analyse de la vidéo: {str(e)}")
        return None

def display_video_info(video_info: Dict[str, Any]) -> None:
    st.success("✅ Vidéo trouvée !")
    if video_info.get("thumbnail"):
        try:
            st.image(video_info["thumbnail"], width=480, use_column_width=True)
        except Exception:
            st.info("🖼️ Aperçu non disponible")
    st.markdown(f"### 🎥 {video_info.get('title', 'Titre non disponible')}")
    duration = video_info.get("duration", 0)
    if duration:
        minutes = duration // 60
        seconds = duration % 60
        st.write(f"⏱️ Durée : {minutes} min {seconds} s")
    else:
        st.write("⏱️ Durée : Non spécifiée")
    if video_info.get("uploader"):
        st.write(f"👤 Auteur : {video_info['uploader']}")
    if video_info.get("extractor_key"):
        st.write(f"📺 Plateforme : {video_info['extractor_key']}")

def download_media_safe(url: str, mode: str, quality: str) -> Optional[Dict[str, Any]]:
    if not DOWNLOADER_AVAILABLE:
        st.error("🔧 Service de téléchargement indisponible.")
        return None
    temp_dir = tempfile.mkdtemp()
    try:
        start_time = time.time()
        file_path = download_media(url, mode, quality, temp_dir)
        download_duration = time.time() - start_time
        if not file_path or not os.path.exists(file_path):
            raise DownloadError("Le fichier téléchargé est introuvable.")
        if os.path.getsize(file_path) == 0:
            raise DownloadError("Le fichier téléchargé est vide.")
        logger.info(f"Successfully downloaded media: {file_path}")
        return {"path": file_path, "size": os.path.getsize(file_path), "duration": download_duration, "temp_dir": temp_dir}
    except Exception as e:
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        error_msg = str(e).lower()
        if "ffmpeg" in error_msg: raise DownloadError("❌ ffmpeg n'est pas installé ou disponible.")
        if "unable to extract" in error_msg: raise DownloadError("❌ Impossible d'extraire les informations de la vidéo. URL non supportée.")
        if "private" in error_msg: raise DownloadError("🔒 Vidéo privée ou restreinte.")
        if "no video formats found" in error_msg: raise DownloadError("❌ Aucun format vidéo trouvé. Vérifiez que la vidéo est publique.")
        raise DownloadError(f"❌ Échec du téléchargement: {str(e)}")

def create_download_link(file_info: Dict[str, Any], mode: str) -> None:
    file_path = file_info['path']
    with open(file_path, "rb") as f:
        file_data = f.read()
    extension = ".mp4" if mode == "Vidéo (MP4)" else ".mp3"
    mime_type = "video/mp4" if mode == "Vidéo (MP4)" else "audio/mpeg"
    file_name = os.path.splitext(os.path.basename(file_path))[0] + extension
    b64_data = base64.b64encode(file_data).decode()
    href = f'<a href="data:{mime_type};base64,{b64_data}" download="{file_name}" id="auto_download_link" style="display: none;">Télécharger</a>'
    st.markdown(href, unsafe_allow_html=True)
    st.components.v1.html("<script>document.getElementById('auto_download_link').click();</script>", height=0)
    st.success(f"✅ Téléchargement réussi! Fichier: {file_name}")

def cleanup_temp_files(file_info: Dict[str, Any]) -> None:
    try:
        if file_info.get('path') and os.path.exists(file_info['path']): os.remove(file_info['path'])
        if file_info.get('temp_dir') and os.path.exists(file_info['temp_dir']): os.rmdir(file_info['temp_dir'])
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")

# ---------------------------
# Main
# ---------------------------

def main():
    setup_page()
    display_system_status()
    if 'video_info' not in st.session_state: st.session_state.video_info = None
    url = st.text_input("🔗 URL de la vidéo :", placeholder="https://www.youtube.com/watch?v=...")
    col1, col2 = st.columns([1, 3])
    with col1: preview_button = st.button("👁️ Prévisualiser la vidéo", type="primary")
    if preview_button: st.session_state.video_info = get_video_info_safe(url)
    if st.session_state.video_info: display_video_info(st.session_state.video_info)
    if st.session_state.video_info or (url and not preview_button):
        st.markdown("---")
        st.subheader("📥 Options de Téléchargement")
        mode = st.radio("Choisissez le format :", ["Vidéo (MP4)", "Audio (MP3)"], horizontal=True)
        quality = "best"
        if mode == "Vidéo (MP4)":
            quality = st.selectbox("Qualité vidéo :", ["best", "720p", "1080p", "480p", "360p"])
        download_button = st.button("🚀 Télécharger", type="primary")
        if download_button:
            try:
                file_info = download_media_safe(url, mode.lower().split()[0], quality.replace('p', ''))
                if file_info:
                    st.success(f"✅ Téléchargement terminé en {file_info['duration']:.1f}s")
                    create_download_link(file_info, mode)
                    cleanup_temp_files(file_info)
            except DownloadError as e:
                st.error(str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                st.error("💥 Erreur inattendue. Veuillez réessayer.")

if __name__ == "__main__":
    main()

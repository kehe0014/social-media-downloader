import os
import time
import streamlit as st
import tempfile
import base64
import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path

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

# Import your modules with proper error handling
try:
    from downloader.yt_utils import get_video_info, download_media
    from downloader.file_utils import ensure_dir
    DOWNLOADER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import downloader modules: {e}")
    DOWNLOADER_AVAILABLE = False
    # Create stub functions for development
    def get_video_info(url):
        raise ImportError("Downloader module not available")
    def download_media(url, media_type, quality, temp_dir):
        raise ImportError("Downloader module not available")
    def ensure_dir(path):
        return Path(path)

class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

class VideoInfoError(Exception):
    """Custom exception for video info retrieval errors."""
    pass

def setup_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Social Media Downloader 🎬",
        layout="centered",
        page_icon="🎬"
    )
    st.title("🎬 Social Media Downloader Pro")
    st.write(
        "Téléchargez des vidéos ou audios depuis Facebook, YouTube, "
        "TikTok, Instagram et bien d'autres plateformes."
    )

def display_system_status() -> None:
    """Display system status in sidebar."""
    with st.sidebar:
        st.header("🔧 Statut du Système")
        if DOWNLOADER_AVAILABLE:
            st.success("✅ Modules de téléchargement disponibles")
        else:
            st.error("❌ Modules de téléchargement non disponibles")
            st.info("Veuillez vérifier l'installation des dépendances.")

def get_video_info_safe(url: str) -> Optional[Dict[str, Any]]:
    """
    Safely retrieve video information with comprehensive error handling.
    
    Args:
        url: The video URL to analyze
        
    Returns:
        Video information dictionary or None if failed
    """
    if not url.strip():
        st.warning("⚠️ Veuillez entrer une URL valide.")
        return None
    
    if not DOWNLOADER_AVAILABLE:
        st.error("🔧 Service temporairement indisponible. Veuillez réessayer plus tard.")
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
        error_msg = f"Erreur lors de l'analyse de la vidéo: {str(e)}"
        logger.error(f"Video info error for {url}: {e}", exc_info=True)
        
        # User-friendly error messages based on exception type
        if "unable to extract" in str(e).lower() or "unsupported url" in str(e).lower():
            st.error("❌ URL non supportée ou inaccessible. Vérifiez le lien et réessayez.")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            st.error("🌐 Erreur de connexion. Vérifiez votre accès internet.")
        elif "private" in str(e).lower() or "restricted" in str(e).lower():
            st.error("🔒 Vidéo privée ou restreinte. Accès non autorisé.")
        else:
            st.error(f"❌ {error_msg}")
            
        return None

def display_video_info(video_info: Dict[str, Any]) -> None:
    """Display video information in a user-friendly format."""
    st.success("✅ Vidéo trouvée !")
    
    # Thumbnail
    if video_info.get("thumbnail"):
        try:
            st.image(video_info["thumbnail"], width=480, use_column_width=True)
        except Exception as e:
            logger.warning(f"Failed to display thumbnail: {e}")
            st.info("🖼️ Aperçu non disponible")
    
    # Video details
    st.markdown(f"### 🎥 {video_info.get('title', 'Titre non disponible')}")
    
    # Duration
    duration = video_info.get("duration", 0)
    if duration:
        minutes = duration // 60
        seconds = duration % 60
        st.write(f"⏱️ Durée : {minutes} min {seconds} s")
    else:
        st.write("⏱️ Durée : Non spécifiée")
    
    # Uploader
    if video_info.get("uploader"):
        st.write(f"👤 Auteur : {video_info['uploader']}")
    
    # Platform
    if video_info.get("extractor_key"):
        st.write(f"📺 Plateforme : {video_info['extractor_key']}")

def download_media_safe(url: str, mode: str, quality: str) -> Optional[Dict[str, Any]]:
    """
    Safely download media with comprehensive error handling.
    
    Args:
        url: Video URL
        mode: Download mode ('video' or 'audio')
        quality: Video quality
        
    Returns:
        Dictionary with file info or None if failed
    """
    if not DOWNLOADER_AVAILABLE:
        st.error("🔧 Service de téléchargement indisponible.")
        return None
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Perform download
        start_time = time.time()
        file_path = download_media(url, mode, quality, temp_dir)
        download_duration = time.time() - start_time
        
        if not file_path or not os.path.exists(file_path):
            raise DownloadError("Le fichier téléchargé est introuvable.")
        
        # Verify file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise DownloadError("Le fichier téléchargé est vide.")
        
        logger.info(f"Successfully downloaded media: {file_path} ({file_size} bytes)")
        
        return {
            'path': file_path,
            'size': file_size,
            'duration': download_duration,
            'temp_dir': temp_dir
        }
        
    except Exception as e:
        # Clean up temporary directory on error
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp directory: {cleanup_error}")
        
        logger.error(f"Download error for {url}: {e}", exc_info=True)
        raise DownloadError(f"Échec du téléchargement: {str(e)}")

def create_download_link(file_info: Dict[str, Any], mode: str) -> None:
    """
    Create and trigger automatic download link.
    
    Args:
        file_info: Dictionary containing file information
        mode: Download mode for MIME type determination
    """
    try:
        file_path = file_info['path']
        
        # Read file data
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Determine file extension and MIME type
        extension = ".mp4" if mode == "Vidéo (MP4)" else ".mp3"
        mime_type = "video/mp4" if mode == "Vidéo (MP4)" else "audio/mpeg"
        
        # Generate filename
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        file_name = f"{base_name}{extension}"
        
        # Encode file for download
        b64_data = base64.b64encode(file_data).decode()
        
        # Create hidden download link
        href = (
            f'<a href="data:{mime_type};base64,{b64_data}" '
            f'download="{file_name}" id="auto_download_link" '
            'style="display: none;">Télécharger</a>'
        )
        st.markdown(href, unsafe_allow_html=True)
        
        # Trigger automatic download via JavaScript
        js_code = """
        <script>
            document.getElementById('auto_download_link').click();
        </script>
        """
        st.components.v1.html(js_code, height=0)
        
        st.success(f"✅ Téléchargement réussi! Fichier: {file_name}")
        
    except Exception as e:
        logger.error(f"Error creating download link: {e}", exc_info=True)
        st.error("❌ Erreur lors de la préparation du téléchargement.")

def cleanup_temp_files(file_info: Dict[str, Any]) -> None:
    """Safely clean up temporary files."""
    try:
        if file_info.get('path') and os.path.exists(file_info['path']):
            os.remove(file_info['path'])
        
        if file_info.get('temp_dir') and os.path.exists(file_info['temp_dir']):
            os.rmdir(file_info['temp_dir'])
            
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")
        # Silently ignore cleanup errors - they're not critical
        
def download_media_safe(url: str, mode: str, quality: str) -> Optional[Dict[str, Any]]:
    """
    Safely download media with comprehensive error handling.
    
    Args:
        url: Video URL
        mode: Download mode ('video' or 'audio')
        quality: Video quality
        
    Returns:
        Dictionary with file info or None if failed
    """
    if not DOWNLOADER_AVAILABLE:
        st.error("🔧 Service de téléchargement indisponible.")
        return None
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Perform download
        start_time = time.time()
        file_path = download_media(url, mode, quality, temp_dir)
        download_duration = time.time() - start_time
        
        if not file_path or not os.path.exists(file_path):
            raise DownloadError("Le fichier téléchargé est introuvable.")
        
        # Verify file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise DownloadError("Le fichier téléchargé est vide.")
        
        logger.info(f"Successfully downloaded media: {file_path} ({file_size} bytes)")
        
        return {
            'path': file_path,
            'size': file_size,
            'duration': download_duration,
            'temp_dir': temp_dir
        }
        
    except Exception as e:
        # Clean up temporary directory on error
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp directory: {cleanup_error}")
        
        logger.error(f"Download error for {url}: {e}", exc_info=True)
        
        # Gestion spécifique des erreurs ffmpeg
        error_msg = str(e).lower()
        if "ffmpeg" in error_msg and "not installed" in error_msg:
            raise DownloadError(
                "❌ Erreur de conversion: ffmpeg n'est pas disponible. "
                "Le service est temporairement indisponible. "
                "Veuillez réessayer plus tard ou contacter l'administrateur."
            )
        elif "unable to extract" in error_msg:
            raise DownloadError("❌ Impossible d'extraire les informations de la vidéo. L'URL est peut-être invalide ou non supportée.")
        elif "private" in error_msg or "restricted" in error_msg:
            raise DownloadError("🔒 Cette vidéo est privée ou restreinte. Accès non autorisé.")
        elif "format" in error_msg and "not available" in error_msg:
            raise DownloadError("📹 La qualité demandée n'est pas disponible pour cette vidéo.")
        else:
            raise DownloadError(f"❌ Échec du téléchargement: {str(e)}")

def main():
    """Main application function."""
    try:
        # Setup
        setup_page()
        display_system_status()
        
        # Initialize session state for video info
        if 'video_info' not in st.session_state:
            st.session_state.video_info = None
        
        # URL input
        url = st.text_input("🔗 URL de la vidéo :", placeholder="https://www.youtube.com/watch?v=...")
        
        # Preview button
        col1, col2 = st.columns([1, 3])
        with col1:
            preview_button = st.button("👁️ Prévisualiser la vidéo", type="primary")
        
        # Handle preview
        if preview_button:
            st.session_state.video_info = get_video_info_safe(url)
        
        # Display video info if available
        if st.session_state.video_info:
            display_video_info(st.session_state.video_info)
        
        # Download section
        if st.session_state.video_info or (url and not preview_button):
            st.markdown("---")
            st.subheader("📥 Options de Téléchargement")
            
            mode = st.radio(
                "Choisissez le format :",
                ["Vidéo (MP4)", "Audio (MP3)"],
                horizontal=True
            )
            
            quality = "best"
            if mode == "Vidéo (MP4)":
                quality = st.selectbox(
                    "Qualité vidéo :",
                    ["best", "720p", "1080p", "480p", "360p"]
                )
            
            download_button = st.button("🚀 Télécharger", type="primary")
            
            if download_button:
                try:
                    file_info = download_media_safe(
                        url, 
                        mode.lower().split()[0], 
                        quality.replace('p', '')
                    )
                    
                    if file_info:
                        st.success(f"✅ Téléchargement terminé en {file_info['duration']:.1f}s")
                        create_download_link(file_info, mode)
                        cleanup_temp_files(file_info)
                        
                except DownloadError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error in download: {e}", exc_info=True)
                    st.error("💥 Erreur inattendue. Veuillez réessayer.")
                    
            
    
    except Exception as e:
        logger.critical(f"Critical application error: {e}", exc_info=True)
        st.error("🚨 Erreur critique de l'application. Veuillez actualiser la page.")

if __name__ == "__main__":
    main()
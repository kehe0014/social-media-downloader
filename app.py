import os
import time
import streamlit as st
from downloader.yt_utils import get_video_info, download_media
from downloader.file_utils import ensure_dir
import tempfile
import base64

OUTPUT_DIR = ensure_dir("downloads")

st.set_page_config(page_title="Social Media Downloader 🎬", layout="centered")
st.title("🎬 Social Media Downloader Pro")
st.write(
    "Téléchargez des vidéos ou audios depuis Facebook, YouTube,"
    "TikTok, Instagram et bien d'autres plateformes."
)

# --- User input ---
url = st.text_input("🔗 URL de la vidéo :")
preview_button = st.button("👁️ Prévisualiser la vidéo")

video_info = None
if preview_button and url:
    try:
        video_info = get_video_info(url)
        st.success("✅ Vidéo trouvée !")
        st.image(video_info.get("thumbnail"), width=480)
        st.markdown(f"### 🎥 {video_info.get('title')}")
        duration = video_info.get("duration", 0)
        minutes = duration // 60
        seconds = duration % 60
        st.write(f"⏱️ Durée : {minutes} min {seconds} s")
        st.write(f"👤 Auteur : {video_info.get('uploader')}")
        st.write(f"📺 Plateforme : {video_info.get('extractor_key')}")
    except Exception as e:
        st.error(f"❌ Impossible d'obtenir les infos : {e}")

# --- Format and quality selection ---
if video_info or (url and not preview_button):
    mode = st.radio("Choisissez le format :", ["Vidéo (MP4)", "Audio (MP3)"])
    quality = "best"
    if mode == "Vidéo (MP4)":
        quality = st.selectbox("Qualité vidéo :", ["best", "720", "1080"])

    download_button = st.button("🚀 Télécharger")

    if download_button:
        try:
            with st.spinner("⏳ Téléchargement en cours..."):
                start = time.time()

                # Download to temporary directory
                temp_dir = tempfile.mkdtemp()
                fichier = download_media(
                    url, mode.lower().split()[0], quality, temp_dir
                )
                duree = time.time() - start
                st.success(f"✅ Téléchargement terminé en {duree:.1f} s")

                # Read the file
                with open(fichier, "rb") as f:
                    file_data = f.read()

                    # Determine file extension and name
                    extension = ".mp4" if mode == "Vidéo (MP4)" else ".mp3"
                    file_name = os.path.basename(fichier)

                    if not file_name.endswith(extension):
                        base_name = os.path.splitext(file_name)[0]
                        file_name = base_name + extension

                    # Encode file to base64 for download
                    b64 = base64.b64encode(file_data).decode()

                    # Create automatic download link
                    mime_type = (
                        "video/mp4" if mode == "Vidéo (MP4)" else "audio/mpeg"
                    )
                    href = (
                        f'<a href="data:{mime_type};base64,{b64}" '
                        f'download="{file_name}" id="auto_download_link" '
                        'style="display: none;">Télécharger</a>'
                    )
                    st.markdown(href, unsafe_allow_html=True)

                    # JavaScript to trigger automatic download
                    js_code = """
                    <script>
                        document.getElementById('auto_download_link').click();
                    </script>
                    """
                    st.components.v1.html(js_code, height=0)

                # Clean up temporary files
                try:
                    os.remove(fichier)
                    os.rmdir(temp_dir)
                except (OSError, FileNotFoundError, PermissionError):
                    # Silently ignore cleanup errors
                    pass

        except Exception as e:
            st.error(f"❌ Erreur lors du téléchargement : {e}")

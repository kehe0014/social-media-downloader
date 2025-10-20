import os
import time
import streamlit as st
from downloader.yt_utils import get_video_info, download_media
from downloader.file_utils import ensure_dir

OUTPUT_DIR = ensure_dir("downloads")

st.set_page_config(page_title="Social Media Downloader 🎬", layout="centered")
st.title("🎬 Social Media Downloader Pro")
st.write(
    "Téléchargez des vidéos ou audios depuis Facebook, YouTube, TikTok, Instagram..."
)

# --- Input utilisateur ---
url = st.text_input("🔗 URL de la vidéo :")
preview_button = st.button("👁️ Prévisualiser la vidéo")

video_info = None
if preview_button and url:
    try:
        video_info = get_video_info(url)
        st.success("✅ Vidéo trouvée !")
        st.image(video_info.get("thumbnail"), width=480)
        st.markdown(f"### 🎥 {video_info.get('title')}")
        st.write(
            f"⏱️ Durée : {video_info.get('duration',0)//60} min {video_info.get('duration',0)%60} s"
        )
        st.write(f"👤 Auteur : {video_info.get('uploader')}")
        st.write(f"📺 Plateforme : {video_info.get('extractor_key')}")
    except Exception as e:
        st.error(f"❌ Impossible d’obtenir les infos : {e}")

# --- Choix du format et qualité ---
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
                fichier = download_media(
                    url, mode.lower().split()[0], quality, OUTPUT_DIR
                )
                duree = time.time() - start
                st.success(f"✅ Téléchargement terminé en {duree:.1f} s")

                with open(fichier, "rb") as f:
                    st.download_button(
                        label="⬇️ Télécharger le fichier",
                        data=f,
                        file_name=os.path.basename(fichier),
                        mime=(
                            "video/mp4"
                            if mode == "Vidéo (MP4)"
                            else "audio/mpeg"
                        ),
                    )
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

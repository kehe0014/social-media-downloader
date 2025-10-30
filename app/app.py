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
st.title("🎬 Social Media Downloader Scrapper Tool")


if not DOWNLOADER_AVAILABLE:
    st.error("❌ yt-dlp is not installed. Please run `pip install yt-dlp`.")
    st.stop()

# URL input
url = st.text_input("🔗 Video URL (Facebook / YouTube / TikTok / Instagram/ Baidu ...)")


def download_video(url, cookies_path=None):
    """Download video with yt-dlp and return the file path."""
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
        raise RuntimeError(f"Download error: {e}")

def create_download_link(file_path):
    """Create a Streamlit download link for the file."""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    fname = os.path.basename(file_path)
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}">📥 Download {fname}</a>'
    st.markdown(href, unsafe_allow_html=True)

if st.button("🚀 Download"):
    if not url.strip():
        st.error("Please enter a valid URL.")
    else:
        try:
            cookies_path = None
            if cookies_file:
                temp_cookies = tempfile.NamedTemporaryFile(delete=False)
                temp_cookies.write(cookies_file.read())
                temp_cookies.close()
                cookies_path = temp_cookies.name

            with st.spinner("Download in progress..."):
                file_path = download_video(url, cookies_path)
            st.success("✅ Download completed!")
            create_download_link(file_path)

        except Exception as e:
            st.error(f"❌ Unable to retrieve the video: {e}")
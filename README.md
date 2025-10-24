# 🎬 Social Media Downloader Pro

**Social Media Downloader Pro** is a modern, professional web application to download videos and audio from multiple social media platforms, including Facebook, YouTube, TikTok, Instagram, and more. It provides both **video (MP4)** and **audio (MP3)** downloads with optional quality selection and preview functionality.

---

## 🚀 Features

- **Web Interface with Streamlit**  
  Easy-to-use UI with video previews, thumbnails, title, duration, and uploader information.
  
- **Video & Audio Downloads**  
  - Download full videos (MP4)  
  - Download only audio (MP3)

- **Quality Selection**  
  Choose the desired video resolution (e.g., 720p, 1080p, best available).

- **Previews**  
  View video thumbnail, title, duration, uploader, and platform before downloading.

- **Modular Architecture**  
  Well-structured Python modules for maintainability and scalability:
  - `downloader/yt_utils.py` – Handles video/audio downloading using `yt-dlp`
  - `downloader/file_utils.py` – Manages directories and file paths
  - `downloader/logger.py` – Logging and colorized console messages
  - `api/download_api.py` – Optional REST API for downloads

- **Optional REST API**  
  Expose download endpoints for integration with other applications.

- **Cross-Platform**  
  Works on Windows, macOS, and Linux (requires Python 3.8+ and FFmpeg).

---

## 📦 Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-username/socialmedia_scrapper.git
cd socialmedia_scrapper

2. **Install dependencies**

```bash
pip install -r requirements.txt

streamlit run app.y


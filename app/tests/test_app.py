import pytest
from unittest.mock import patch, MagicMock
from downloader.yt_utils import get_video_info, download_media
from downloader.file_utils import ensure_dir
import os


# --- Test ensure_dir ---
def test_ensure_dir(tmp_path):
    dir_path = tmp_path / "downloads"
    result = ensure_dir(str(dir_path))
    assert result == str(dir_path)
    assert dir_path.exists()


# --- Mock get_video_info pour tests ---
@patch("downloader.yt_utils.YoutubeDL.extract_info")
def test_get_video_info(mock_extract):
    mock_extract.return_value = {
        "title": "Test Video",
        "duration": 120,
        "uploader": "TestUploader",
        "extractor_key": "youtube",
        "thumbnail": "http://example.com/thumb.jpg",
    }
    url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
    info = get_video_info(url)
    assert info["title"] == "Test Video"
    assert info["duration"] == 120
    assert info["uploader"] == "TestUploader"
    assert info["extractor_key"] == "youtube"
    assert info["thumbnail"] == "http://example.com/thumb.jpg"


# --- Test que le module peut être importé ---
def test_import_app():
    import app.app as app

    assert hasattr(app, "st")

"""
Configuration settings for the Telegram watermark bot.
"""

import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7628459480:AAH-5SlJj5Yvw44ro9ms_Yf0oYO-WbWUKwE")

# Watermark configuration
WATERMARK_TEXT = "TG @supplywalah"
SITE_TEXT = "Supplywalah.blogspot.com"

# File size limits (150MB in bytes)
MAX_FILE_SIZE = 150 * 1024 * 1024

# Temporary file settings
TEMP_DIR = "/tmp/telegram_bot"

# FFmpeg settings
FONT_SIZE_BASE = 24  # Base font size, will be adjusted based on video resolution
FONT_COLOR = "white"
FONT_OUTLINE_COLOR = "black"
FONT_OUTLINE_WIDTH = 2

# Messages
MESSAGES = {
    'start': "Welcome! Send me a video file (up to 150MB) and I'll add watermarks.",
    'processing': "🔄 Applying watermark to your video...",
    'uploading': "⬆️ Uploading watermarked video...",
    'complete': "✅ Video processed and sent successfully!",
    'error_file_size': "❌ Error: File size exceeds 150MB limit.",
    'error_not_video': "❌ Error: Please send a video file.",
    'error_processing': "❌ Error: Failed to process video. Please try again.",
    'error_download': "❌ Error: Failed to download video. Please try again.",
    'error_upload': "❌ Error: Failed to send video. Please try again.",
    'error_general': "❌ An unexpected error occurred. Please try again later."
}

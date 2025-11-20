#!/usr/bin/env python3
"""
Simple Telegram watermark bot implementation.
"""
import os
import logging
import tempfile
import subprocess
from pathlib import Path
from keep_alive import start_server_thread

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "7628459480:AAH-5SlJj5Yvw44ro9ms_Yf0oYO-WbWUKwE"
WATERMARK_TEXT = "TG @supplywalah"
SITE_TEXT = "Supplywalah.blogspot.com"
MAX_FILE_SIZE = 150 * 1024 * 1024  # 150MB user upload limit
TEMP_DIR = "/tmp/telegram_bot"

# Create temp directory
os.makedirs(TEMP_DIR, exist_ok=True)

def get_video_dimensions(video_path):
    """Get video dimensions using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                return int(stream['width']), int(stream['height'])
        return 1920, 1080  # fallback
    except:
        return 1920, 1080  # fallback

def calculate_font_size(width, height):
    """Calculate font size based on video dimensions."""
    min_dimension = min(width, height)
    if min_dimension >= 1080:
        return 48
    elif min_dimension >= 720:
        return 36
    elif min_dimension >= 480:
        return 28
    else:
        return 20

def apply_watermarks(input_path, output_path):
    """Apply watermarks to video using ffmpeg."""
    try:
        width, height = get_video_dimensions(input_path)
        font_size = calculate_font_size(width, height)
        
        logger.info(f"Processing {width}x{height} video with font size {font_size}")
        
        # FFmpeg command to add watermarks
        cmd = [
            'ffmpeg', '-i', input_path, '-y',
            '-vf', 
            f"drawtext=text='{WATERMARK_TEXT}':fontsize={font_size}:fontcolor=white:borderw=2:bordercolor=black:x=w-tw-{font_size//2}:y=h-th-{font_size//2},"
            f"drawtext=text='{SITE_TEXT}':fontsize={font_size}:fontcolor=white:borderw=2:bordercolor=black:x=(w-tw)/2:y={font_size//2}",
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-c:a', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Watermarks applied successfully")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error applying watermarks: {e}")
        return False

def handle_webhook():
    """Simple webhook handler for basic testing."""
    import urllib.request
    import json
    
    # Get updates
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        if data['ok'] and data['result']:
            for update in data['result']:
                process_update(update)
                
    except Exception as e:
        logger.error(f"Error getting updates: {e}")

def process_update(update):
    """Process a single telegram update."""
    try:
        if 'message' not in update:
            return
            
        message = update['message']
        chat_id = message['chat']['id']
        
        if 'text' in message and message['text'].startswith('/start'):
            send_message(chat_id, "Welcome! Send me a video file (up to 150MB) and I'll add watermarks.\n\nWatermarks added:\n• 'TG @supplywalah' - bottom right\n• 'Supplywalah.blogspot.com' - top center")
            return
            
        # Handle video files
        if 'video' in message:
            handle_video(message['video'], chat_id)
        elif 'document' in message and message['document'].get('mime_type', '').startswith('video/'):
            handle_video(message['document'], chat_id)
        else:
            send_message(chat_id, "Please send a video file.")
            
    except Exception as e:
        logger.error(f"Error processing update: {e}")

def handle_video(video_info, chat_id):
    """Handle video processing."""
    try:
        # Check file size
        file_size = video_info.get('file_size', 0)
        if file_size > MAX_FILE_SIZE:
            send_message(chat_id, "❌ Error: File size exceeds 150MB limit.")
            return
            
        # Log file size for processing
        file_size_mb = file_size // 1024 // 1024 if file_size > 0 else 0
        logger.info(f"Video size: {file_size_mb}MB")
            
        send_message(chat_id, "🔄 Applying watermark to your video...")
        
        # Download and process video
        file_id = video_info['file_id']
        logger.info(f"Processing file_id: {file_id}, size: {file_size} bytes ({file_size//1024//1024}MB)")
        
        input_path, output_path = download_and_process_video(file_id)
        
        if output_path and os.path.exists(output_path):
            # Send processed video back through Telegram
            send_video(chat_id, output_path)
        else:
            send_message(chat_id, "❌ Error: Failed to process video.")
            
        # Cleanup
        for path in [input_path, output_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                    logger.info(f"Cleaned up {path}")
                except:
                    pass
                
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        send_message(chat_id, "❌ An error occurred while processing your video.")

def download_and_process_video(file_id):
    """Download and process video file."""
    try:
        import urllib.request
        import urllib.error
        import json
        
        # Get file info
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        logger.info(f"Getting file info from: {url}")
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                logger.info(f"File info response received successfully")
        except urllib.error.HTTPError as e:
            try:
                error_content = e.read().decode()
                logger.error(f"HTTP Error {e.code} getting file info: {error_content}")
            except:
                logger.error(f"HTTP Error {e.code} getting file info - no error details")
            return None, None
            
        if not data.get('ok'):
            logger.error(f"Failed to get file info: {data}")
            return None, None
            
        file_path = data['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        logger.info(f"Download URL: {download_url}")
        
        # Download file
        input_path = os.path.join(TEMP_DIR, f"input_{file_id[:10]}.mp4")
        
        try:
            # Try curl first for large file support
            curl_cmd = ['curl', '-L', '-o', input_path, download_url]
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(input_path) and os.path.getsize(input_path) > 0:
                logger.info(f"Successfully downloaded with curl: {os.path.getsize(input_path)} bytes")
            else:
                # Fallback to urllib if curl fails
                logger.info("Curl failed, trying urllib fallback...")
                req = urllib.request.Request(download_url)
                with urllib.request.urlopen(req, timeout=300) as response:
                    with open(input_path, 'wb') as f:
                        # Download in chunks for large files
                        chunk_size = 8192
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                logger.info(f"Downloaded with urllib: {os.path.getsize(input_path)} bytes")
                
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None, None
        
        logger.info(f"Downloaded video to {input_path}")
        
        # Process video
        output_path = os.path.join(TEMP_DIR, f"output_{file_id[:10]}.mp4")
        success = apply_watermarks(input_path, output_path)
        
        if success:
            return input_path, output_path
        else:
            return input_path, None
            
    except Exception as e:
        logger.error(f"Error downloading/processing video: {e}")
        return None, None

def send_message(chat_id, text):
    """Send text message to chat."""
    try:
        import urllib.request
        import urllib.parse
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': text
        }).encode()
        
        req = urllib.request.Request(url, data=data, method='POST')
        urllib.request.urlopen(req)
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")

def send_video(chat_id, video_path):
    """Send video file back to chat."""
    try:
        import urllib.request
        
        send_message(chat_id, "⬆️ Uploading watermarked video...")
        
        # Prepare video upload
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
        
        # Read video file
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        
        # Create multipart form data
        import uuid
        boundary = str(uuid.uuid4())
        
        body = b''
        body += f'--{boundary}\r\n'.encode()
        body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        body += f'{chat_id}\r\n'.encode()
        
        body += f'--{boundary}\r\n'.encode()
        body += b'Content-Disposition: form-data; name="video"; filename="watermarked_video.mp4"\r\n'
        body += b'Content-Type: video/mp4\r\n\r\n'
        body += video_data
        body += b'\r\n'
        
        body += f'--{boundary}--\r\n'.encode()
        
        # Send request
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        
        with urllib.request.urlopen(req, timeout=300) as response:
            logger.info("Video sent successfully")
            send_message(chat_id, "✅ Video processed and sent successfully!")
            
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        send_message(chat_id, "❌ Error: Failed to send video. Please try again.")

def run_polling():
    """Simple polling implementation."""
    import time
    import urllib.request
    import json
    
    last_update_id = 0
    logger.info("Starting bot polling...")
    
    while True:
        try:
            # Get updates
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            if last_update_id > 0:
                url += f"?offset={last_update_id + 1}"
                
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if data['ok'] and data['result']:
                for update in data['result']:
                    process_update(update)
                    last_update_id = max(last_update_id, update['update_id'])
                    
            time.sleep(1)  # Poll every second
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying

if __name__ == '__main__':
    # Start keep-alive web server for UptimeRobot
    start_server_thread()
    
    # Start bot polling
    run_polling()
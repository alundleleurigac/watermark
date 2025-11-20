"""
Telegram bot implementation for video watermarking.
"""

import os
import tempfile
import logging
from typing import Optional

from telegram._update import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

from config import (
    BOT_TOKEN, 
    WATERMARK_TEXT, 
    SITE_TEXT, 
    MAX_FILE_SIZE, 
    MESSAGES
)
from video_processor import VideoProcessor

logger = logging.getLogger(__name__)

class TelegramWatermarkBot:
    """Main bot class handling Telegram interactions."""
    
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.video_processor = VideoProcessor()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.VIDEO, self.handle_video)
        )
        self.application.add_handler(
            MessageHandler(filters.ATTACHMENT, self.handle_document) 
        )
        self.application.add_handler(
            MessageHandler(~filters.COMMAND, self.handle_other_messages)
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(MESSAGES['start'])
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "🎥 Video Watermark Bot\n\n"
            "Send me a video file (up to 150MB) and I'll add watermarks:\n"
            f"• '{WATERMARK_TEXT}' - bottom right\n"
            f"• '{SITE_TEXT}' - top center\n\n"
            "Supported formats: MP4, AVI, MOV, MKV, etc.\n"
            "The bot works with both landscape and portrait videos."
        )
        await update.message.reply_text(help_text)
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video messages."""
        message = update.message
        video = message.video
        
        # Check file size
        if video.file_size > MAX_FILE_SIZE:
            await message.reply_text(MESSAGES['error_file_size'])
            return
        
        await self._process_video_file(message, video.get_file)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages (videos sent as files)."""
        message = update.message
        document = message.document
        
        # Check if it's a video file
        if not document.mime_type or not document.mime_type.startswith('video/'):
            await message.reply_text(MESSAGES['error_not_video'])
            return
        
        # Check file size
        if document.file_size > MAX_FILE_SIZE:
            await message.reply_text(MESSAGES['error_file_size'])
            return
        
        await self._process_video_file(message, document.get_file)
    
    async def handle_other_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-video messages."""
        await update.message.reply_text(MESSAGES['error_not_video'])
    
    async def _process_video_file(self, message, get_file_func):
        """
        Process video file with watermarks.
        
        Args:
            message: Telegram message object
            get_file_func: Function to get file from Telegram
        """
        processing_message = None
        input_path = None
        output_path = None
        
        try:
            # Send processing message
            processing_message = await message.reply_text(MESSAGES['processing'])
            
            # Download video file
            try:
                file = await get_file_func()
                
                # Create temporary input file
                input_fd, input_path = tempfile.mkstemp(
                    suffix='.mp4',
                    dir=self.video_processor.temp_dir,
                    prefix='input_'
                )
                os.close(input_fd)
                
                # Download file from Telegram
                await file.download_to_drive(input_path)
                logger.info(f"Downloaded video to: {input_path}")
                
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                await processing_message.edit_text(MESSAGES['error_download'])
                return
            
            # Process video with watermarks
            try:
                output_path = self.video_processor.process_video(
                    input_path, WATERMARK_TEXT, SITE_TEXT
                )
                
                if not output_path:
                    await processing_message.edit_text(MESSAGES['error_processing'])
                    return
                
            except Exception as e:
                logger.error(f"Error processing video: {e}")
                await processing_message.edit_text(MESSAGES['error_processing'])
                return
            
            # Send processed video back to user
            try:
                await processing_message.edit_text(MESSAGES['complete'])
                
                with open(output_path, 'rb') as video_file:
                    await message.reply_video(
                        video=video_file,
                        supports_streaming=True,
                        caption="✅ Watermarked video ready!"
                    )
                
                logger.info(f"Successfully sent watermarked video to user {message.from_user.id}")
                
            except Exception as e:
                logger.error(f"Error sending video: {e}")
                await message.reply_text(MESSAGES['error_general'])
                
        except Exception as e:
            logger.error(f"Unexpected error in video processing: {e}")
            if processing_message:
                await processing_message.edit_text(MESSAGES['error_general'])
            else:
                await message.reply_text(MESSAGES['error_general'])
        
        finally:
            # Clean up temporary files
            if input_path:
                self.video_processor.cleanup_file(input_path)
            if output_path:
                self.video_processor.cleanup_file(output_path)
    
    def start(self):
        """Start the bot."""
        logger.info("Starting Telegram watermark bot...")
        
        # Create temp directory
        os.makedirs(self.video_processor.temp_dir, exist_ok=True)
        
        # Start the bot with polling
        self.application.run_polling(
            drop_pending_updates=True
        )
    

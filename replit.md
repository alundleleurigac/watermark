# Overview

This is a Telegram bot that automatically applies watermarks to video files. Users can send video files (up to 150MB) to the bot, and it will process the video with branded watermarks then send the watermarked video back through Telegram. The bot uses FFmpeg for video processing.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Telegram Bot API Integration**: Uses python-telegram-bot library for handling Telegram interactions
- **Asynchronous Processing**: Built with async/await patterns for handling multiple concurrent requests
- **Handler-based Architecture**: Separate handlers for commands (/start, /help) and message types (video, documents)

## Video Processing Pipeline
- **FFmpeg Integration**: Core video processing using ffmpeg-python wrapper
- **Watermark Application**: Applies dual watermarks (text-based) to videos:
  - Primary watermark: "TG @supplywalah" 
  - Secondary watermark: "Supplywalah.blogspot.com"
- **Dynamic Font Sizing**: Automatically adjusts watermark size based on video resolution
- **Quality Preservation**: Maintains original video quality while adding watermarks

## File Management
- **Temporary File System**: Uses `/tmp/telegram_bot` directory for processing
- **Size Validation**: 150MB file size limit enforcement
- **Format Validation**: Accepts video files and video documents/attachments
- **Cleanup Strategy**: Temporary files are managed during processing lifecycle
- **Upload System**: Processed videos are sent back to users via Telegram

## Configuration Management
- **Environment Variables**: Bot token and settings configurable via environment
- **Centralized Config**: Single config.py file for all application settings
- **Message Templates**: Predefined response messages for different scenarios

## Error Handling
- **Graceful Degradation**: Comprehensive error handling for file operations, video processing, and network issues
- **User Feedback**: Specific error messages for different failure scenarios
- **Logging**: Structured logging for debugging and monitoring

# External Dependencies

## Core Services
- **Telegram Bot API**: Primary interface for receiving messages, sending status updates, and delivering processed videos
- **FFmpeg**: Video processing engine for watermark application

## Python Libraries
- **python-telegram-bot**: Telegram API wrapper and bot framework
- **ffmpeg-python**: Python wrapper for FFmpeg operations
- **asyncio**: Asynchronous programming support

## System Requirements
- **FFmpeg Binary**: Must be installed on the system for video processing
- **File System Access**: Requires write permissions to `/tmp` directory for temporary file storage

## Configuration Dependencies
- **BOT_TOKEN**: Telegram bot authentication token (required)
- **System Environment**: Unix-like system with temporary directory support
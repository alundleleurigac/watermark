#!/usr/bin/env python3
"""
Main entry point for the Telegram watermark bot.
"""

import logging
from bot import TelegramWatermarkBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot."""
    try:
        bot = TelegramWatermarkBot()
        bot.start()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()

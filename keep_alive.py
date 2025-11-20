#!/usr/bin/env python3
"""
Simple web server to keep the bot alive for UptimeRobot monitoring.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import threading

logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    def do_GET(self):
        """Handle GET requests."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot Status</title>
        </head>
        <body>
            <h1>✅ Bot is Running!</h1>
            <p>The Telegram watermark bot is active and ready to process videos.</p>
            <p>Send a video to your Telegram bot to test it!</p>
        </body>
        </html>
        """
        self.wfile.write(message.encode())
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs to keep console clean."""
        pass

def run_server(port=5000):
    """Run the keep-alive web server."""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, KeepAliveHandler)
    logger.info(f"Keep-alive server running on port {port}")
    httpd.serve_forever()

def start_server_thread():
    """Start the web server in a background thread."""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info("Keep-alive server started in background")

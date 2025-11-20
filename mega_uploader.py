#!/usr/bin/env python3
"""
Mega.nz uploader utility for the Telegram watermark bot using megatools.
"""
import os
import logging
import subprocess
import tempfile
from config import MEGA_EMAIL, MEGA_PASSWORD, MEGA_FOLDER_NAME

logger = logging.getLogger(__name__)

class MegaUploader:
    """Handles file uploads to Mega.nz using megatools command-line utility."""
    
    def __init__(self):
        """Initialize Mega uploader."""
        self.config_file = None
        self.setup_config()
        
    def setup_config(self):
        """Create megatools configuration file."""
        try:
            if not MEGA_EMAIL or not MEGA_PASSWORD:
                logger.error("Mega.nz credentials not configured")
                return False
                
            # Create a temporary config file for megatools
            config_content = f"""[Login]
Username = {MEGA_EMAIL}
Password = {MEGA_PASSWORD}
"""
            
            # Create config file in temp directory
            config_fd, self.config_file = tempfile.mkstemp(suffix='.conf', prefix='mega_')
            os.close(config_fd)
            
            with open(self.config_file, 'w') as f:
                f.write(config_content)
                
            logger.info("Mega.nz configuration file created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Mega.nz config: {e}")
            return False
    
    def upload_file(self, file_path, original_filename=None):
        """Upload file to Mega.nz using megatools."""
        try:
            if not self.config_file or not os.path.exists(self.config_file):
                return False, "Mega.nz configuration not available"
                
            if not os.path.exists(file_path):
                return False, "File to upload does not exist"
                
            # Generate filename if not provided
            if not original_filename:
                original_filename = f"watermarked_{os.path.basename(file_path)}"
            
            # Create the target path in Mega.nz
            remote_path = f"/{MEGA_FOLDER_NAME}/{original_filename}"
            
            logger.info(f"Uploading {file_path} as {remote_path} to Mega.nz")
            
            # Use megatools to upload file
            cmd = [
                'megaput',
                '--config', self.config_file,
                '--path', remote_path,
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"Successfully uploaded {original_filename} to Mega.nz")
                return True, f"File uploaded successfully as {original_filename}"
            else:
                logger.error(f"Upload failed: {result.stderr}")
                return False, f"Upload failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            logger.error("Upload timeout - file too large or connection slow")
            return False, "Upload timeout"
        except Exception as e:
            logger.error(f"Error uploading file to Mega.nz: {e}")
            return False, f"Upload error: {str(e)}"
    
    def check_tools_available(self):
        """Check if megatools is available."""
        try:
            result = subprocess.run(['megaput', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_upload_stats(self):
        """Get basic account info using megatools."""
        try:
            if not self.config_file:
                return "Configuration not available"
                
            cmd = ['megadf', '--config', self.config_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return f"Mega.nz status: {result.stdout.strip()}"
            else:
                return "Stats unavailable"
                
        except Exception as e:
            logger.error(f"Error getting Mega stats: {e}")
            return "Stats unavailable"
    
    def cleanup(self):
        """Clean up temporary config file."""
        if self.config_file and os.path.exists(self.config_file):
            try:
                os.unlink(self.config_file)
                logger.info("Cleaned up Mega.nz config file")
            except Exception as e:
                logger.error(f"Error cleaning up config file: {e}")

# Global uploader instance
mega_uploader = MegaUploader()
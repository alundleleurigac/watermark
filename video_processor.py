"""
Video processing module for applying watermarks using FFmpeg.
"""

import os
import tempfile
import ffmpeg
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Handles video watermarking operations."""
    
    def __init__(self):
        self.temp_dir = "/tmp/telegram_bot"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def get_video_info(self, input_path: str) -> Tuple[int, int, float]:
        """
        Get video dimensions and duration.
        
        Args:
            input_path: Path to input video file
            
        Returns:
            Tuple of (width, height, duration)
        """
        try:
            probe = ffmpeg.probe(input_path)
            video_stream = next(
                stream for stream in probe['streams'] 
                if stream['codec_type'] == 'video'
            )
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            duration = float(video_stream.get('duration', 0))
            return width, height, duration
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    def calculate_font_size(self, width: int, height: int) -> int:
        """
        Calculate appropriate font size based on video resolution.
        
        Args:
            width: Video width
            height: Video height
            
        Returns:
            Font size in pixels
        """
        # Use the smaller dimension as reference to ensure text fits
        min_dimension = min(width, height)
        
        # Scale font size based on resolution
        if min_dimension >= 1080:
            return 48
        elif min_dimension >= 720:
            return 36
        elif min_dimension >= 480:
            return 28
        else:
            return 20
    
    def apply_watermarks(self, input_path: str, output_path: str, 
                        watermark_text: str, site_text: str) -> bool:
        """
        Apply watermarks to video using FFmpeg.
        
        Args:
            input_path: Path to input video
            output_path: Path for output video
            watermark_text: Bottom right watermark text
            site_text: Top center watermark text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get video information
            width, height, duration = self.get_video_info(input_path)
            font_size = self.calculate_font_size(width, height)
            
            logger.info(f"Processing video: {width}x{height}, font_size: {font_size}")
            
            # Calculate positions
            # Bottom right watermark position (with padding)
            bottom_right_x = f"w-tw-{font_size//2}"  # Right edge minus text width minus padding
            bottom_right_y = f"h-th-{font_size//2}"  # Bottom edge minus text height minus padding
            
            # Top center watermark position
            top_center_x = "(w-tw)/2"  # Centered horizontally
            top_center_y = str(font_size//2)  # Top edge plus padding
            
            # Create filter complex for dual watermarks
            filter_complex = [
                # First watermark (bottom right)
                f"drawtext=text='{watermark_text}'"
                f":fontsize={font_size}"
                f":fontcolor=white"
                f":borderw=2"
                f":bordercolor=black"
                f":x={bottom_right_x}"
                f":y={bottom_right_y}"
                f":font=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                
                # Second watermark (top center) 
                f"drawtext=text='{site_text}'"
                f":fontsize={font_size}"
                f":fontcolor=white"
                f":borderw=2"
                f":bordercolor=black"
                f":x={top_center_x}"
                f":y={top_center_y}"
                f":font=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ]
            
            # Build FFmpeg command
            input_stream = ffmpeg.input(input_path)
            
            # Apply video filters
            video = input_stream.video.filter('drawtext', 
                text=watermark_text,
                fontsize=font_size,
                fontcolor='white',
                borderw=2,
                bordercolor='black',
                x=bottom_right_x,
                y=bottom_right_y,
                fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            ).filter('drawtext',
                text=site_text,
                fontsize=font_size,
                fontcolor='white', 
                borderw=2,
                bordercolor='black',
                x=top_center_x,
                y=top_center_y,
                fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            )
            
            # Copy audio stream
            audio = input_stream.audio
            
            # Output with same codec to maintain quality
            out = ffmpeg.output(
                video, audio, output_path,
                vcodec='libx264',
                acodec='aac',
                preset='medium',
                crf=23
            )
            
            # Run FFmpeg command
            ffmpeg.run(out, overwrite_output=True, quiet=True)
            
            logger.info(f"Successfully applied watermarks to video")
            return True
            
        except Exception as e:
            logger.error(f"Error applying watermarks: {e}")
            return False
    
    def process_video(self, input_path: str, watermark_text: str, site_text: str) -> Optional[str]:
        """
        Process video with watermarks and return output path.
        
        Args:
            input_path: Path to input video
            watermark_text: Bottom right watermark text
            site_text: Top center watermark text
            
        Returns:
            Path to processed video or None if failed
        """
        try:
            # Create temporary output file
            output_fd, output_path = tempfile.mkstemp(
                suffix='.mp4', 
                dir=self.temp_dir,
                prefix='watermarked_'
            )
            os.close(output_fd)  # Close file descriptor, we just need the path
            
            # Apply watermarks
            success = self.apply_watermarks(input_path, output_path, watermark_text, site_text)
            
            if success:
                return output_path
            else:
                # Clean up failed output file
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return None
    
    def cleanup_file(self, file_path: str):
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

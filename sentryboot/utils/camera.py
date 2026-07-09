import os
import sys
import uuid
import time
from pathlib import Path
from typing import Optional

def capture_snapshot(output_dir: Path) -> Optional[Path]:
    """Detects if a usable webcam is available, captures a single snapshot,
    and saves it to the output directory.
    
    Args:
        output_dir: Dedicated directory to save the snapshot file.
        
    Returns:
        Path: The absolute path of the saved JPEG file if successful, or None if failed.
    """
    try:
        import cv2
    except ImportError:
        # OpenCV not installed or missing
        return None
        
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Filesystem write permission issues
        return None
        
    cap = None
    try:
        # cv2.VideoCapture(0) opens the default camera.
        # On Windows, cv2.CAP_DSHOW prevents slow camera initialization.
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
        
        if not cap.isOpened():
            return None
            
        # Set a standard low-to-medium resolution (640x480) to reduce file and base64 size.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Allow auto-exposure and white balance to calibrate (warm-up time)
        time.sleep(0.5)
        
        # Read frame
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
            
        # Generate unique filename using timestamp and a short UUID suffix
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"intruder_{timestamp}_{unique_id}.jpg"
        filepath = output_dir.resolve() / filename
        
        # Save image with standard JPEG compression quality of 80
        success = cv2.imwrite(str(filepath), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if success and filepath.exists():
            return filepath
            
    except Exception:
        pass
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
                
    return None

"""
Background tasks for camera monitoring and face detection processing.
This module handles continuous camera monitoring, face detection, and
attendance recording without blocking the main API thread.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import cv2
import numpy as np

from utils.logging import get_logger
from utils.security import get_db_manager
from core.fts_system import FaceTrackingPipeline
from app.config import settings

logger = get_logger(__name__)

class CameraMonitor:
    """
    Background camera monitor for continuous face detection and attendance tracking.
    """
    
    def __init__(self):
        self.active_cameras: Dict[int, bool] = {}
        self.camera_threads: Dict[int, threading.Thread] = {}
        self.pipeline = None
        self.db_manager = get_db_manager()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._stop_event = threading.Event()
        
    def start_camera_monitoring(self, camera_id: int) -> bool:
        """
        Start monitoring a specific camera for face detection.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            True if monitoring started successfully
        """
        if camera_id in self.active_cameras and self.active_cameras[camera_id]:
            logger.warning(f"Camera {camera_id} is already being monitored")
            return False
        
        try:
            # Initialize pipeline if not exists
            if self.pipeline is None:
                self.pipeline = FaceTrackingPipeline()
            
            # Mark camera as active
            self.active_cameras[camera_id] = True
            
            # Start monitoring thread
            thread = threading.Thread(
                target=self._monitor_camera,
                args=(camera_id,),
                daemon=True,
                name=f"camera_monitor_{camera_id}"
            )
            self.camera_threads[camera_id] = thread
            thread.start()
            
            logger.info(f"Started monitoring camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring camera {camera_id}: {e}")
            self.active_cameras[camera_id] = False
            return False
    
    def stop_camera_monitoring(self, camera_id: int) -> bool:
        """
        Stop monitoring a specific camera.
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            True if monitoring stopped successfully
        """
        if camera_id not in self.active_cameras or not self.active_cameras[camera_id]:
            logger.warning(f"Camera {camera_id} is not being monitored")
            return False
        
        try:
            # Mark camera as inactive
            self.active_cameras[camera_id] = False
            
            # Wait for thread to finish
            if camera_id in self.camera_threads:
                thread = self.camera_threads[camera_id]
                thread.join(timeout=5.0)  # Wait up to 5 seconds
                del self.camera_threads[camera_id]
            
            logger.info(f"Stopped monitoring camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring camera {camera_id}: {e}")
            return False
    
    def stop_all_monitoring(self):
        """Stop monitoring all cameras."""
        self._stop_event.set()
        
        camera_ids = list(self.active_cameras.keys())
        for camera_id in camera_ids:
            self.stop_camera_monitoring(camera_id)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Stopped all camera monitoring")
    
    def get_active_cameras(self) -> List[int]:
        """Get list of currently monitored cameras."""
        return [cam_id for cam_id, active in self.active_cameras.items() if active]
    
    def _monitor_camera(self, camera_id: int):
        """
        Main monitoring loop for a specific camera.
        
        Args:
            camera_id: Camera identifier
        """
        logger.info(f"Starting camera monitoring loop for camera {camera_id}")
        
        cap = None
        frame_count = 0
        last_detection_time = time.time()
        
        try:
            # Initialize camera
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                logger.error(f"Failed to open camera {camera_id}")
                return
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, settings.FRAME_RATE)
            
            while self.active_cameras.get(camera_id, False) and not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from camera {camera_id}")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                current_time = time.time()
                
                # Process every 10th frame to reduce CPU load
                if frame_count % 10 == 0:
                    # Submit face detection task to thread pool
                    future = self.executor.submit(
                        self._process_frame,
                        frame,
                        camera_id,
                        current_time
                    )
                    
                    # Don't wait for result to avoid blocking
                    # Results are processed in the background
                
                # Log detection rate every 30 seconds
                if current_time - last_detection_time > 30:
                    logger.debug(f"Camera {camera_id} processed {frame_count} frames")
                    last_detection_time = current_time
                    frame_count = 0
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Error in camera monitoring loop for camera {camera_id}: {e}")
        
        finally:
            if cap:
                cap.release()
            self.active_cameras[camera_id] = False
            logger.info(f"Camera monitoring stopped for camera {camera_id}")
    
    def _process_frame(self, frame: np.ndarray, camera_id: int, timestamp: float):
        """
        Process a single frame for face detection and recognition.
        
        Args:
            frame: Camera frame
            camera_id: Camera identifier
            timestamp: Frame timestamp
        """
        try:
            start_time = time.time()
            
            # Detect faces using the pipeline
            faces = self.pipeline.detect_faces(frame)
            
            processing_time = time.time() - start_time
            
            if faces:
                logger.debug(f"Camera {camera_id}: Detected {len(faces)} faces")
                
                # Process each detected face
                for face_data in faces:
                    self._handle_face_detection(face_data, camera_id, timestamp)
            
            # Log performance metrics
            if len(faces) > 0:
                from utils.logging import log_face_detection
                log_face_detection(logger, camera_id, len(faces), processing_time)
                
        except Exception as e:
            logger.error(f"Error processing frame from camera {camera_id}: {e}")
    
    def _handle_face_detection(self, face_data: Dict, camera_id: int, timestamp: float):
        """
        Handle a detected face - identify and record attendance.
        
        Args:
            face_data: Face detection data
            camera_id: Camera identifier
            timestamp: Detection timestamp
        """
        try:
            # Extract face information
            employee_id = face_data.get('employee_id')
            confidence = face_data.get('confidence', 0.0)
            
            if employee_id and confidence > settings.FACE_RECOGNITION_TOLERANCE:
                # Record attendance
                self.db_manager.record_attendance(
                    employee_id=employee_id,
                    camera_id=camera_id,
                    confidence_score=confidence,
                    event_type='entry',  # Could be 'entry' or 'exit'
                    timestamp=timestamp
                )
                
                logger.info(
                    f"Recorded attendance for employee {employee_id} "
                    f"on camera {camera_id} with confidence {confidence:.3f}"
                )
            
        except Exception as e:
            logger.error(f"Error handling face detection: {e}")

class StreamManager:
    """
    Manager for active video streams to prevent resource conflicts.
    """
    
    def __init__(self):
        self.active_streams: Dict[int, int] = {}  # camera_id -> stream_count
        self.max_streams_per_camera = 3
        
    @contextmanager
    def get_stream(self, camera_id: int):
        """
        Context manager for managing camera streams.
        
        Args:
            camera_id: Camera identifier
            
        Yields:
            Camera stream if available
            
        Raises:
            RuntimeError: If too many streams are active
        """
        current_streams = self.active_streams.get(camera_id, 0)
        
        if current_streams >= self.max_streams_per_camera:
            raise RuntimeError(f"Too many active streams for camera {camera_id}")
        
        # Increment stream count
        self.active_streams[camera_id] = current_streams + 1
        
        try:
            # Initialize camera
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                raise RuntimeError(f"Failed to open camera {camera_id}")
            
            yield cap
            
        finally:
            # Cleanup
            cap.release()
            
            # Decrement stream count
            self.active_streams[camera_id] -= 1
            if self.active_streams[camera_id] <= 0:
                del self.active_streams[camera_id]
    
    def get_active_stream_count(self, camera_id: int) -> int:
        """Get number of active streams for a camera."""
        return self.active_streams.get(camera_id, 0)
    
    def get_total_streams(self) -> int:
        """Get total number of active streams."""
        return sum(self.active_streams.values())

# Global instances
camera_monitor = CameraMonitor()
stream_manager = StreamManager()

def start_background_monitoring():
    """Start background camera monitoring for all configured cameras."""
    try:
        # Start monitoring default camera
        camera_monitor.start_camera_monitoring(settings.DEFAULT_CAMERA_ID)
        logger.info("Background camera monitoring started")
    except Exception as e:
        logger.error(f"Failed to start background monitoring: {e}")

def stop_background_monitoring():
    """Stop all background monitoring."""
    try:
        camera_monitor.stop_all_monitoring()
        logger.info("Background camera monitoring stopped")
    except Exception as e:
        logger.error(f"Error stopping background monitoring: {e}")
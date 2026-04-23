def start(self, width: int = 960, height: int = 540, fps: int = 60) -> bool:
        """Initialize and start video capture"""
        try:
            if platform.system() == "Windows":
                # Windows-specific capture methods.
                # MSMF (Media Foundation) is preferred — DirectShow often
                # caps at 30fps even when the camera supports 60fps.
                capture_methods = [
                    (self.device_index, cv2.CAP_MSMF),   # Media Foundation first
                    (self.device_index, cv2.CAP_DSHOW),   # DirectShow fallback
                    (self.device_index, cv2.CAP_ANY),
                    (0, cv2.CAP_ANY),
                ]

                for dev_id, backend in capture_methods:
                    try:
                        self.cap = cv2.VideoCapture(dev_id, backend)
                        if self.cap.isOpened():
                            break
                        self.cap.release()
                    except Exception:
                        continue
            else:
                # Unix-like systems (Linux/Mac) capture method
                self.cap = cv2.VideoCapture(self.device_index)

            if not self.cap or not self.cap.isOpened():
                raise RuntimeError("Failed to open camera")

            # Try MJPEG first — avoids USB bandwidth limits with
            # uncompressed YUV at high resolutions.  Falls back silently
            # if the camera/backend doesn't support it.
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            # Request desired resolution and frame rate
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)

            # Read back resolution (usually reliable)
            self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # CAP_PROP_FPS is unreliable on DirectShow — often reports 30
            # even when the camera delivers 60.  Measure empirically by
            # timing a burst of frames.
            reported_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.actual_fps = self._measure_fps(warmup=10, sample=30,
                                                fallback=reported_fps or fps)

            print(f"[VideoCapturer] {self.actual_width}x{self.actual_height} "
                  f"@ {self.actual_fps:.1f}fps (reported={reported_fps:.0f})",
                  flush=True)

            self.is_running = True
            return True

        except Exception as e:
            print(f"Failed to start capture: {str(e)}")
            if self.cap:
                self.cap.release()
            return False
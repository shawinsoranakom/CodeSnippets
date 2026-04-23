def update(self, i: int, cap: cv2.VideoCapture, stream: str):
        """Read stream frames in daemon thread and update image buffer."""
        n, f = 0, self.frames[i]  # frame number, frame array
        while self.running and cap.isOpened() and n < (f - 1):
            if len(self.imgs[i]) < 30:  # keep a <=30-image buffer
                n += 1
                cap.grab()  # .read() = .grab() followed by .retrieve()
                if n % self.vid_stride == 0:
                    success, im = cap.retrieve()
                    im = (
                        cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[..., None] if self.cv2_flag == cv2.IMREAD_GRAYSCALE else im
                    )
                    if not success:
                        im = np.zeros(self.shape[i], dtype=np.uint8)
                        LOGGER.warning("Video stream unresponsive, please check your IP camera connection.")
                        cap.open(stream)  # re-open stream if signal was lost
                    if self.buffer:
                        self.imgs[i].append(im)
                    else:
                        self.imgs[i] = [im]
            else:
                time.sleep(0.01)
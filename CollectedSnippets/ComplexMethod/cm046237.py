def __next__(self) -> tuple[list[str], list[np.ndarray], list[str]]:
        """Return the next batch of images or video frames with their paths and metadata."""
        paths, imgs, info = [], [], []
        while len(imgs) < self.bs:
            if self.count >= self.nf:  # end of file list
                if imgs:
                    return paths, imgs, info  # return last partial batch
                else:
                    raise StopIteration

            path = self.files[self.count]
            if self.video_flag[self.count]:
                self.mode = "video"
                if not self.cap or not self.cap.isOpened():
                    self._new_video(path)

                success = False
                for _ in range(self.vid_stride):
                    success = self.cap.grab()
                    if not success:
                        break  # end of video or failure

                if success:
                    success, im0 = self.cap.retrieve()
                    im0 = (
                        cv2.cvtColor(im0, cv2.COLOR_BGR2GRAY)[..., None]
                        if self.cv2_flag == cv2.IMREAD_GRAYSCALE
                        else im0
                    )
                    if success:
                        self.frame += 1
                        paths.append(path)
                        imgs.append(im0)
                        info.append(f"video {self.count + 1}/{self.nf} (frame {self.frame}/{self.frames}) {path}: ")
                        if self.frame == self.frames:  # end of video
                            self.count += 1
                            self.cap.release()
                else:
                    # Move to the next file if the current video ended or failed to open
                    self.count += 1
                    if self.cap:
                        self.cap.release()
                    if self.count < self.nf:
                        self._new_video(self.files[self.count])
            else:
                # Handle image files
                self.mode = "image"
                im0 = imread(path, flags=self.cv2_flag)  # BGR
                if im0 is None:
                    LOGGER.warning(f"Image Read Error {path}")
                else:
                    paths.append(path)
                    imgs.append(im0)
                    info.append(f"image {self.count + 1}/{self.nf} {path}: ")
                self.count += 1  # move to the next file
                if self.count >= self.ni:  # end of image list
                    break

        return paths, imgs, info
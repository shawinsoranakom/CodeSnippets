def _release_resources(self) -> None:
        """Release all acquired resources safely"""
        # iov must be released before ioring and shm
        for attr in ("iov_r", "iov_w", "ior_r", "ior_w"):
            obj = getattr(self, attr, None)
            if obj is not None:
                del obj
                setattr(self, attr, None)

        for attr in ("shm_r", "shm_w"):
            shm = getattr(self, attr, None)
            if shm is not None:
                try:
                    shm.close()
                except Exception as e:
                    logger.warning("Failed to close %s: %s", attr, e)
                setattr(self, attr, None)

        if self.file is not None:
            try:
                deregister_fd(self.file)
            except Exception as e:
                logger.warning("deregister_fd failed: %s", e)
            try:
                os.close(self.file)
            except OSError as e:
                logger.warning("os.close failed: %s", e)
            self.file = None
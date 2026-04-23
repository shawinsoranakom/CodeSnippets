def acquire(self, timeout: float = 1.0) -> bool:
        """Acquire the lock for this port.

        Args:
            timeout: Maximum time to wait for the lock

        Returns:
            True if lock was acquired, False otherwise
        """
        if self._locked:
            return True

        try:
            if HAS_FCNTL:
                # Unix-style file locking with fcntl
                self.lock_fd = os.open(
                    self.lock_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC
                )

                # Try to acquire exclusive lock with timeout
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        self._locked = True

                        # Write port number to lock file for debugging
                        os.write(self.lock_fd, f'{self.port}\n'.encode())
                        os.fsync(self.lock_fd)

                        logger.debug(f'Acquired lock for port {self.port}')
                        return True
                    except (OSError, IOError):
                        # Lock is held by another process, wait a bit
                        time.sleep(0.01)

                # Timeout reached
                if self.lock_fd:
                    os.close(self.lock_fd)
                    self.lock_fd = None
                return False
            else:
                # Windows fallback: use atomic file creation
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        # Try to create lock file exclusively
                        self.lock_fd = os.open(
                            self.lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                        )
                        self._locked = True

                        # Write port number to lock file for debugging
                        os.write(self.lock_fd, f'{self.port}\n'.encode())
                        os.fsync(self.lock_fd)

                        logger.debug(f'Acquired lock for port {self.port}')
                        return True
                    except OSError:
                        # Lock file already exists, wait a bit
                        time.sleep(0.01)

                # Timeout reached
                return False

        except Exception as e:
            logger.debug(f'Failed to acquire lock for port {self.port}: {e}')
            if self.lock_fd:
                try:
                    os.close(self.lock_fd)
                except OSError:
                    pass
                self.lock_fd = None
            return False
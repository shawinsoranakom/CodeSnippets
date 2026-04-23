def dec_thread_sharing(self):
        with self._thread_sharing_lock:
            if self._thread_sharing_count <= 0:
                raise RuntimeError(
                    "Cannot decrement the thread sharing count below zero."
                )
            self._thread_sharing_count -= 1
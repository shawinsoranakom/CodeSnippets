def allow_thread_sharing(self):
        with self._thread_sharing_lock:
            return self._thread_sharing_count > 0
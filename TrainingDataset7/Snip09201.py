def inc_thread_sharing(self):
        with self._thread_sharing_lock:
            self._thread_sharing_count += 1
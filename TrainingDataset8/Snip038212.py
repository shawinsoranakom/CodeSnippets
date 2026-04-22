def _get_next_file_id(self) -> int:
        """Return the next file ID and increment our ID counter."""
        with self._file_id_lock:
            file_id = self._file_id_counter
            self._file_id_counter += 1
            return file_id
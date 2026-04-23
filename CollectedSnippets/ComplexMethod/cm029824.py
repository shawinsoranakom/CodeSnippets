def add(self, message):
        """Add message and return assigned key."""
        keys = self.keys()
        if len(keys) == 0:
            new_key = 1
        else:
            new_key = max(keys) + 1
        new_path = os.path.join(self._path, str(new_key))
        f = _create_carefully(new_path)
        closed = False
        try:
            if self._locked:
                _lock_file(f)
            try:
                try:
                    self._dump_message(message, f)
                except BaseException:
                    # Unlock and close so it can be deleted on Windows
                    if self._locked:
                        _unlock_file(f)
                    _sync_close(f)
                    closed = True
                    os.remove(new_path)
                    raise
                if isinstance(message, MHMessage):
                    self._dump_sequences(message, new_key)
            finally:
                if self._locked:
                    _unlock_file(f)
        finally:
            if not closed:
                _sync_close(f)
        return new_key
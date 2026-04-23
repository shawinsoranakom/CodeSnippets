def get_message(self, key):
        """Return a Message representation or raise a KeyError."""
        try:
            if self._locked:
                f = open(os.path.join(self._path, str(key)), 'rb+')
            else:
                f = open(os.path.join(self._path, str(key)), 'rb')
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise KeyError('No message with key: %s' % key)
            else:
                raise
        with f:
            if self._locked:
                _lock_file(f)
            try:
                msg = MHMessage(f)
            finally:
                if self._locked:
                    _unlock_file(f)
        for name, key_list in self.get_sequences().items():
            if key in key_list:
                msg.add_sequence(name)
        return msg
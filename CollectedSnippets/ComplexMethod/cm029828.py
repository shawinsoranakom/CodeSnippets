def pack(self):
        """Re-name messages to eliminate numbering gaps. Invalidates keys."""
        sequences = self.get_sequences()
        prev = 0
        changes = []
        for key in self.iterkeys():
            if key - 1 != prev:
                changes.append((key, prev + 1))
                try:
                    os.link(os.path.join(self._path, str(key)),
                            os.path.join(self._path, str(prev + 1)))
                except (AttributeError, PermissionError):
                    os.rename(os.path.join(self._path, str(key)),
                              os.path.join(self._path, str(prev + 1)))
                else:
                    os.unlink(os.path.join(self._path, str(key)))
            prev += 1
        self._next_key = prev + 1
        if len(changes) == 0:
            return
        for name, key_list in sequences.items():
            for old, new in changes:
                if old in key_list:
                    key_list[key_list.index(old)] = new
        self.set_sequences(sequences)
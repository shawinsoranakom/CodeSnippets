def pop(self):
        """Pop off the last frame we created, and restore all the old values."""

        idx = self.frames.pop()
        for key, val in self.stack[idx:]:
            if val is self._cell_delete_obj:
                del self.values[key]
            else:
                self.values[key] = val
        self.stack = self.stack[:idx]
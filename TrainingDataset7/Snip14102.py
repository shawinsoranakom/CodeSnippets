def _is_callback(self, name):
        if not self._populated:
            self._populate()
        return name in self._callback_strs
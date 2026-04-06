def previous(self):
        self._realise()
        self._index = (self._index - 1) % len(self._commands)
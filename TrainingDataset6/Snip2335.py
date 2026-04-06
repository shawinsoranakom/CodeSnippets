def _realise(self):
        if not self._realised:
            self._commands += list(self._commands_gen)
            self._realised = True
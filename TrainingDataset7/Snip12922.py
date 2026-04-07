def _assert_mutable(self):
        if not self._mutable:
            raise AttributeError("This QueryDict instance is immutable")
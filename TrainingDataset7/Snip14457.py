def inner(self, *args):
        if (_wrapped := self._wrapped) is empty:
            self._setup()
            _wrapped = self._wrapped
        return func(_wrapped, *args)
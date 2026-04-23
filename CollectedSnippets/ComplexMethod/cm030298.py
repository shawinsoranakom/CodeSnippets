def __new__(cls, id, /, _whence=None, _ownsref=None):
        # There is only one instance for any given ID.
        if not isinstance(id, int):
            raise TypeError(f'id must be an int, got {id!r}')
        id = int(id)
        if _whence is None:
            if _ownsref:
                _whence = _interpreters.WHENCE_STDLIB
            else:
                _whence = _interpreters.whence(id)
        assert _whence in cls._WHENCE_TO_STR, repr(_whence)
        if _ownsref is None:
            _ownsref = (_whence == _interpreters.WHENCE_STDLIB)
        try:
            self = _known[id]
            assert hasattr(self, '_ownsref')
        except KeyError:
            self = super().__new__(cls)
            _known[id] = self
            self._id = id
            self._whence = _whence
            self._ownsref = _ownsref
            if _ownsref:
                # This may raise InterpreterNotFoundError:
                _interpreters.incref(id)
        return self
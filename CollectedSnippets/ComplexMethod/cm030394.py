def _get_child_mock(self, /, **kw):
        """Create the child mocks for attributes and return value.
        By default child mocks will be the same type as the parent.
        Subclasses of Mock may want to override this to customize the way
        child mocks are made.

        For non-callable mocks the callable variant will be used (rather than
        any custom subclass)."""
        if self._mock_sealed:
            attribute = f".{kw['name']}" if "name" in kw else "()"
            mock_name = self._extract_mock_name() + attribute
            raise AttributeError(mock_name)

        _new_name = kw.get("_new_name")
        if _new_name in self.__dict__['_spec_asyncs']:
            return AsyncMock(**kw)

        _type = type(self)
        if issubclass(_type, MagicMock) and _new_name in _async_method_magics:
            # Any asynchronous magic becomes an AsyncMock
            klass = AsyncMock
        elif issubclass(_type, AsyncMockMixin):
            if (_new_name in _all_sync_magics or
                    self._mock_methods and _new_name in self._mock_methods):
                # Any synchronous method on AsyncMock becomes a MagicMock
                klass = MagicMock
            else:
                klass = AsyncMock
        elif not issubclass(_type, CallableMixin):
            if issubclass(_type, NonCallableMagicMock):
                klass = MagicMock
            elif issubclass(_type, NonCallableMock):
                klass = Mock
        else:
            klass = _type.__mro__[1]
        return klass(**kw)
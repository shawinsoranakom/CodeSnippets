def __setattr__(self, name, value):
        if name in _allowed_names:
            # property setters go through here
            return object.__setattr__(self, name, value)
        elif (self._spec_set and self._mock_methods is not None and
            name not in self._mock_methods and
            name not in self.__dict__):
            raise AttributeError("Mock object has no attribute '%s'" % name)
        elif name in _unsupported_magics:
            msg = 'Attempting to set unsupported magic method %r.' % name
            raise AttributeError(msg)
        elif name in _all_magics:
            if self._mock_methods is not None and name not in self._mock_methods:
                raise AttributeError("Mock object has no attribute '%s'" % name)

            if not _is_instance_mock(value):
                setattr(type(self), name, _get_method(name, value))
                original = value
                value = lambda *args, **kw: original(self, *args, **kw)
            else:
                # only set _new_name and not name so that mock_calls is tracked
                # but not method calls
                _check_and_set_parent(self, value, None, name)
                setattr(type(self), name, value)
                self._mock_children[name] = value
        elif name == '__class__':
            self._spec_class = value
            return
        else:
            if _check_and_set_parent(self, value, name, name):
                self._mock_children[name] = value

        if self._mock_sealed and not hasattr(self, name):
            mock_name = f'{self._extract_mock_name()}.{name}'
            raise AttributeError(f'Cannot set {mock_name}')

        if isinstance(value, PropertyMock):
            self.__dict__[name] = value
            return
        return object.__setattr__(self, name, value)
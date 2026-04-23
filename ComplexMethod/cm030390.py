def __getattr__(self, name):
        if name in {'_mock_methods', '_mock_unsafe'}:
            raise AttributeError(name)
        elif self._mock_methods is not None:
            if name not in self._mock_methods or name in _all_magics:
                raise AttributeError("Mock object has no attribute %r" % name)
        elif _is_magic(name):
            raise AttributeError(name)
        if not self._mock_unsafe and (not self._mock_methods or name not in self._mock_methods):
            if name.startswith(('assert', 'assret', 'asert', 'aseert', 'assrt')) or name in _ATTRIB_DENY_LIST:
                raise AttributeError(
                    f"{name!r} is not a valid assertion. Use a spec "
                    f"for the mock if {name!r} is meant to be an attribute")

        with NonCallableMock._lock:
            result = self._mock_children.get(name)
            if result is _deleted:
                raise AttributeError(name)
            elif result is None:
                wraps = None
                if self._mock_wraps is not None:
                    # XXXX should we get the attribute without triggering code
                    # execution?
                    wraps = getattr(self._mock_wraps, name)

                result = self._get_child_mock(
                    parent=self, name=name, wraps=wraps, _new_name=name,
                    _new_parent=self
                )
                self._mock_children[name]  = result

            elif isinstance(result, _SpecState):
                try:
                    result = create_autospec(
                        result.spec, result.spec_set, result.instance,
                        result.parent, result.name
                    )
                except InvalidSpecError:
                    target_name = self.__dict__['_mock_name'] or self
                    raise InvalidSpecError(
                        f'Cannot autospec attr {name!r} from target '
                        f'{target_name!r} as it has already been mocked out. '
                        f'[target={self!r}, attr={result.spec!r}]')
                self._mock_children[name]  = result

        return result
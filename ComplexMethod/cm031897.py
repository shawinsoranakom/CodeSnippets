def __getitem__(self, key):
        # XXX Be more exact for the 3-tuple case?
        if type(key) not in (str, tuple):
            raise KeyError(f'unsupported key {key!r}')
        resolved, extra = self._resolve_key(key)
        if extra:
            raise KeyError(f'key must have at most 3 parts, got {key!r}')
        if not resolved[2]:
            raise ValueError(f'expected name in key, got {key!r}')
        try:
            return self._decls[resolved]
        except KeyError:
            if type(key) is tuple and len(key) == 3:
                filename, funcname, name = key
            else:
                filename, funcname, name = resolved
            if filename and not filename.endswith(('.c', '.h')):
                raise KeyError(f'invalid filename in key {key!r}')
            elif funcname and funcname.endswith(('.c', '.h')):
                raise KeyError(f'invalid funcname in key {key!r}')
            elif name and name.endswith(('.c', '.h')):
                raise KeyError(f'invalid name in key {key!r}')
            else:
                raise
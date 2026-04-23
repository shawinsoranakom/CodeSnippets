def find(self, *key, **explicit):
        if not key:
            if not explicit:
                return iter(self)
            return self._find(**explicit)

        resolved, extra = self._resolve_key(key)
        filename, funcname, name = resolved
        if not extra:
            kind = None
        elif len(extra) == 1:
            kind, = extra
        else:
            raise KeyError(f'key must have at most 4 parts, got {key!r}')

        implicit= {}
        if filename:
            implicit['filename'] = filename
        if funcname:
            implicit['funcname'] = funcname
        if name:
            implicit['name'] = name
        if kind:
            implicit['kind'] = kind
        return self._find(**implicit, **explicit)
def get_group(cls, kind, *, groups=None):
        if not isinstance(kind, cls):
            raise TypeError(f'expected KIND, got {kind!r}')
        if groups is None:
            groups = ['type']
        elif not groups:
            groups = ()
        elif isinstance(groups, str):
            group = groups
            if group not in cls._GROUPS:
                raise ValueError(f'unsupported group {group!r}')
            groups = [group]
        else:
            unsupported = [g for g in groups if g not in cls._GROUPS]
            if unsupported:
                raise ValueError(f'unsupported groups {", ".join(repr(unsupported))}')
        for group in groups:
            if kind in cls._GROUPS[group]:
                return group
        else:
            return kind.value
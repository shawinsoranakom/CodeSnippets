def __init__(self, item, typedecl=None, **extra):
        assert item is not None
        self.item = item
        if typedecl in (UNKNOWN, IGNORED):
            pass
        elif item.kind is KIND.STRUCT or item.kind is KIND.UNION:
            if isinstance(typedecl, TypeDeclaration):
                raise NotImplementedError(item, typedecl)
            elif typedecl is None:
                typedecl = UNKNOWN
            else:
                typedecl = [UNKNOWN if d is None else d for d in typedecl]
        elif typedecl is None:
            typedecl = UNKNOWN
        elif typedecl and not isinstance(typedecl, TypeDeclaration):
            # All the other decls have a single type decl.
            typedecl, = typedecl
            if typedecl is None:
                typedecl = UNKNOWN
        self.typedecl = typedecl
        self._extra = extra
        self._locked = True

        self._validate()
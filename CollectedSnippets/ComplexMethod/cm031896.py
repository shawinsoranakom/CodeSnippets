def _resolve_key(cls, raw):
        if isinstance(raw, str):
            raw = [raw]
        elif isinstance(raw, Declaration):
            raw = (
                raw.filename if cls._is_public(raw) else None,
                # `raw.parent` is always None for types and functions.
                raw.parent if raw.kind is KIND.VARIABLE else None,
                raw.name,
            )

        extra = None
        if len(raw) == 1:
            name, = raw
            if name:
                name = str(name)
                if name.endswith(('.c', '.h')):
                    # This is only legit as a query.
                    key = (name, None, None)
                else:
                    key = (None, None, name)
            else:
                key = (None, None, None)
        elif len(raw) == 2:
            parent, name = raw
            name = str(name)
            if isinstance(parent, Declaration):
                key = (None, parent.name, name)
            elif not parent:
                key = (None, None, name)
            else:
                parent = str(parent)
                if parent.endswith(('.c', '.h')):
                    key = (parent, None, name)
                else:
                    key = (None, parent, name)
        else:
            key, extra = raw[:3], raw[3:]
            filename, funcname, name = key
            filename = str(filename) if filename else None
            if isinstance(funcname, Declaration):
                funcname = funcname.name
            else:
                funcname = str(funcname) if funcname else None
            name = str(name) if name else None
            key = (filename, funcname, name)
        return key, extra
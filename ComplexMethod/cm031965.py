def _normalize(cls, spec):
        if len(spec) == 1:
            raw, = spec
            raise NotImplementedError
            return _resolve_column(raw)

        if len(spec) == 4:
            label, field, width, fmt = spec
            if width:
                if not fmt:
                    fmt = str(width)
                elif _parse_fmt(fmt)[0] != width:
                    raise ValueError(f'width mismatch in {spec}')
        elif len(raw) == 3:
            label, field, fmt = spec
            if not field:
                label, field = None, label
            elif not isinstance(field, str) or not field.isidentifier():
                # XXX This doesn't seem right...
                fmt = f'{field}:{fmt}' if fmt else field
                label, field = None, label
        elif len(raw) == 2:
            label = None
            field, fmt = raw
            if not field:
                field, fmt = fmt, None
            elif not field.isidentifier() or fmt.isidentifier():
                label, field = field, fmt
        else:
            raise NotImplementedError

        fmt = f':{fmt}' if fmt else ''
        if label:
            return cls._parse(f'[{label}]{field}{fmt}')
        else:
            return cls._parse(f'{field}{fmt}')
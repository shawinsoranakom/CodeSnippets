def _parse(cls, specstr):
        m = cls.REGEX.match(specstr)
        if not m:
            return None
        (label, field,
         align, width1,
         width2, fmt,
         ) = m.groups()
        if not label:
            label = field
        if fmt:
            assert not align and not width1, (specstr,)
            _parsed = _parse_fmt(fmt)
            if not _parsed:
                raise NotImplementedError
            elif width2:
                width, _ = _parsed
                if width != int(width2):
                    raise NotImplementedError(specstr)
        elif width2:
            fmt = width2
            width = int(width2)
        else:
            assert not fmt, (fmt, specstr)
            if align:
                width = int(width1) if width1 else len(label)
                fmt = f'{align}{width}'
            else:
                width = None
        return field, label, fmt, width
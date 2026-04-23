def _parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
                   encoding='utf-8', errors='replace'):
        qs, _coerce_result = qs, compat_str
        pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
        r = []
        for name_value in pairs:
            if not name_value and not strict_parsing:
                continue
            nv = name_value.split('=', 1)
            if len(nv) != 2:
                if strict_parsing:
                    raise ValueError('bad query field: %r' % (name_value,))
                # Handle case of a control-name with no equal sign
                if keep_blank_values:
                    nv.append('')
                else:
                    continue
            if len(nv[1]) or keep_blank_values:
                name = nv[0].replace('+', ' ')
                name = compat_urllib_parse_unquote(
                    name, encoding=encoding, errors=errors)
                name = _coerce_result(name)
                value = nv[1].replace('+', ' ')
                value = compat_urllib_parse_unquote(
                    value, encoding=encoding, errors=errors)
                value = _coerce_result(value)
                r.append((name, value))
        return r
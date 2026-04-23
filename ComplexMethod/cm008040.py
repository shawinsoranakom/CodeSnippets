def create_key(outer_mobj):
            if not outer_mobj.group('has_key'):
                return outer_mobj.group(0)
            key = outer_mobj.group('key')
            mobj = re.match(INTERNAL_FORMAT_RE, key)
            value, replacement, default, last_field = None, None, na, ''
            while mobj:
                mobj = mobj.groupdict()
                default = mobj['default'] if mobj['default'] is not None else default
                value = get_value(mobj)
                last_field, replacement = mobj['fields'], mobj['replacement']
                if value is None and mobj['alternate']:
                    mobj = re.match(INTERNAL_FORMAT_RE, mobj['remaining'][1:])
                else:
                    break

            if None not in (value, replacement):
                try:
                    value = replacement_formatter.format(replacement, value)
                except ValueError:
                    value, default = None, na

            fmt = outer_mobj.group('format')
            if fmt == 's' and last_field in field_size_compat_map and isinstance(value, int):
                fmt = f'0{field_size_compat_map[last_field]:d}d'

            flags = outer_mobj.group('conversion') or ''
            str_fmt = f'{fmt[:-1]}s'
            if value is None:
                value, fmt = default, 's'
            elif fmt[-1] == 'l':  # list
                delim = '\n' if '#' in flags else ', '
                value, fmt = delim.join(map(str, variadic(value, allowed_types=(str, bytes)))), str_fmt
            elif fmt[-1] == 'j':  # json
                value, fmt = json.dumps(
                    value, default=_dumpjson_default,
                    indent=4 if '#' in flags else None, ensure_ascii='+' not in flags), str_fmt
            elif fmt[-1] == 'h':  # html
                value, fmt = escapeHTML(str(value)), str_fmt
            elif fmt[-1] == 'q':  # quoted
                value = map(str, variadic(value) if '#' in flags else [value])
                value, fmt = shell_quote(value, shell=True), str_fmt
            elif fmt[-1] == 'B':  # bytes
                value = f'%{str_fmt}'.encode() % str(value).encode()
                value, fmt = value.decode('utf-8', 'ignore'), 's'
            elif fmt[-1] == 'U':  # unicode normalized
                value, fmt = unicodedata.normalize(
                    # "+" = compatibility equivalence, "#" = NFD
                    'NF{}{}'.format('K' if '+' in flags else '', 'D' if '#' in flags else 'C'),
                    value), str_fmt
            elif fmt[-1] == 'D':  # decimal suffix
                num_fmt, fmt = fmt[:-1].replace('#', ''), 's'
                value = format_decimal_suffix(value, f'%{num_fmt}f%s' if num_fmt else '%d%s',
                                              factor=1024 if '#' in flags else 1000)
            elif fmt[-1] == 'S':  # filename sanitization
                value, fmt = filename_sanitizer(last_field, value, restricted='#' in flags), str_fmt
            elif fmt[-1] == 'c':
                if value:
                    value = str(value)[0]
                else:
                    fmt = str_fmt
            elif fmt[-1] not in 'rsa':  # numeric
                value = float_or_none(value)
                if value is None:
                    value, fmt = default, 's'

            if sanitize:
                # If value is an object, sanitize might convert it to a string
                # So we manually convert it before sanitizing
                if fmt[-1] == 'r':
                    value, fmt = repr(value), str_fmt
                elif fmt[-1] == 'a':
                    value, fmt = ascii(value), str_fmt
                if fmt[-1] in 'csra':
                    value = sanitize(last_field, value)

            key = '{}\0{}'.format(key.replace('%', '%\0'), outer_mobj.group('format'))
            TMPL_DICT[key] = value
            return '{prefix}%({key}){fmt}'.format(key=key, fmt=fmt, prefix=outer_mobj.group('prefix'))
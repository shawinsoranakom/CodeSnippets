def get_value(mdict):
            # Object traversal
            value = _traverse_infodict(mdict['fields'])
            # Negative
            if mdict['negate']:
                value = float_or_none(value)
                if value is not None:
                    value *= -1
            # Do maths
            offset_key = mdict['maths']
            if offset_key:
                value = float_or_none(value)
                operator = None
                while offset_key:
                    item = re.match(
                        MATH_FIELD_RE if operator else MATH_OPERATORS_RE,
                        offset_key).group(0)
                    offset_key = offset_key[len(item):]
                    if operator is None:
                        operator = MATH_FUNCTIONS[item]
                        continue
                    item, multiplier = (item[1:], -1) if item[0] == '-' else (item, 1)
                    offset = float_or_none(item)
                    if offset is None:
                        offset = float_or_none(_traverse_infodict(item))
                    try:
                        value = operator(value, multiplier * offset)
                    except (TypeError, ZeroDivisionError):
                        return None
                    operator = None
            # Datetime formatting
            if mdict['strf_format']:
                value = strftime_or_none(value, mdict['strf_format'].replace('\\,', ','))

            # XXX: Workaround for https://github.com/yt-dlp/yt-dlp/issues/4485
            if sanitize and value == '':
                value = None
            return value
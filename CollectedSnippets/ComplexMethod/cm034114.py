def check_type_dict(value):
    """Verify that value is a dict or convert it to a dict and return it.

    Raises :class:`TypeError` if unable to convert to a dict

    :arg value: Dict or string to convert to a dict. Accepts ``k1=v2, k2=v2`` or ``k1=v2 k2=v2``.

    :returns: value converted to a dictionary
    """
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        if value.startswith("{"):
            try:
                return json.loads(value)
            except Exception:
                try:
                    result = literal_eval(value)
                except Exception:
                    pass
                else:
                    if isinstance(result, dict):
                        return result
                raise TypeError('unable to evaluate string as dictionary')
        elif '=' in value:
            fields = []
            field_buffer = []
            in_quote = False
            in_escape = False
            for c in value.strip():
                if in_escape:
                    field_buffer.append(c)
                    in_escape = False
                elif c == '\\':
                    in_escape = True
                elif not in_quote and c in ('\'', '"'):
                    in_quote = c
                elif in_quote and in_quote == c:
                    in_quote = False
                elif not in_quote and c in (',', ' '):
                    field = ''.join(field_buffer)
                    if field:
                        fields.append(field)
                    field_buffer = []
                else:
                    field_buffer.append(c)

            field = ''.join(field_buffer)
            if field:
                fields.append(field)
            try:
                return dict(x.split("=", 1) for x in fields)
            except ValueError:
                # no "=" to split on: "k1=v1, k2"
                raise TypeError('unable to evaluate string in the "key=value" format as dictionary')
        else:
            raise TypeError("dictionary requested, could not parse JSON or key=value")

    raise TypeError('%s cannot be converted to a dict' % type(value))
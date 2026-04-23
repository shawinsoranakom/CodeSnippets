def _cleanup_from_default(type_, value):
    if not value:
        if type_ == 'one2many':
            return O2MValue()
        elif type_ == 'many2many':
            return M2MValue()
        elif type_ in ('integer', 'float'):
            return 0
        return value

    if type_ == 'one2many':
        raise NotImplementedError()
    elif type_ == 'datetime' and isinstance(value, datetime):
        return fields.Datetime.to_string(value)
    elif type_ == 'date' and isinstance(value, date):
        return fields.Date.to_string(value)
    return value
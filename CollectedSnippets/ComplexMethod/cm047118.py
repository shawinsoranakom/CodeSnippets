def convert_read_to_form(values, model_fields):
    result = {}
    for fname, value in values.items():
        field_info = {'type': 'id'} if fname == 'id' else model_fields[fname]
        if field_info['type'] == 'one2many':
            if 'edition_view' in field_info:
                subfields = field_info['edition_view']['fields']
                value = O2MValue(convert_read_to_form(vals, subfields) for vals in (value or ()))
            else:
                value = O2MValue({'id': id_} for id_ in (value or ()))
        elif field_info['type'] == 'many2many':
            value = M2MValue({'id': id_} for id_ in (value or ()))
        elif field_info['type'] == 'datetime' and isinstance(value, datetime):
            value = fields.Datetime.to_string(value)
        elif field_info['type'] == 'date' and isinstance(value, date):
            value = fields.Date.to_string(value)
        result[fname] = value
    return result
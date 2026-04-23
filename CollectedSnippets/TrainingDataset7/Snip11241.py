def unnest(fields):
    result = []

    for field in fields:
        if isinstance(field, CompositePrimaryKey):
            result.extend(field.fields)
        else:
            result.append(field)

    return result
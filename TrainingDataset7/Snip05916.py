def lookup_field(name, obj, model_admin=None):
    opts = obj._meta
    try:
        f = _get_non_gfk_field(opts, name)
    except (FieldDoesNotExist, FieldIsAForeignKeyColumnName):
        # For non-regular field values, the value is either a method,
        # property, related field, or returned via a callable.
        f = None
        if callable(name):
            attr = name
            value = attr(obj)
        elif hasattr(model_admin, name) and name != "__str__":
            attr = getattr(model_admin, name)
            value = attr(obj)
        else:
            sentinel = object()
            attr = getattr(obj, name, sentinel)
            if callable(attr):
                value = attr()
            else:
                if attr is sentinel:
                    attr = obj
                    for part in name.split(LOOKUP_SEP):
                        attr = getattr(attr, part, sentinel)
                        if attr is sentinel:
                            return None, None, None
                    # The final field is needed for displaying boolean icons.
                    if LOOKUP_SEP in name:
                        f = get_fields_from_path(opts.model, name)[-1]
                value = attr
            if hasattr(model_admin, "model") and hasattr(model_admin.model, name):
                attr = getattr(model_admin.model, name)
    else:
        attr = None
        value = getattr(obj, name)
    return f, attr, value
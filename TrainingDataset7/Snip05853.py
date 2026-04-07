def _coerce_field_name(field_name, field_index):
    """
    Coerce a field_name (which may be a callable) to a string.
    """
    if callable(field_name):
        if field_name.__name__ == "<lambda>":
            return "lambda" + str(field_index)
        else:
            return field_name.__name__
    return field_name
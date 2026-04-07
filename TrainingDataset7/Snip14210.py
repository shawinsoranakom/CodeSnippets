def flatten_choices(choices):
    """Flatten choices by removing nested values."""
    for value_or_group, label_or_nested in choices or ():
        if isinstance(label_or_nested, (list, tuple)):
            yield from label_or_nested
        else:
            yield value_or_group, label_or_nested
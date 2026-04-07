def unlocalize(value):
    """
    Force a value to be rendered as a non-localized value.
    """
    return str(formats.localize(value, use_l10n=False))
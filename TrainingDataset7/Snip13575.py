def localize(value):
    """
    Force a value to be rendered as a localized value.
    """
    return str(formats.localize(value, use_l10n=True))
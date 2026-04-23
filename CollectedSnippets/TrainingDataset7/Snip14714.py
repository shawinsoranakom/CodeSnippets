def ngettext(singular, plural, number):
    """
    Return a string of the translation of either the singular or plural,
    based on the number.
    """
    return do_ntranslate(singular, plural, number, "ngettext")
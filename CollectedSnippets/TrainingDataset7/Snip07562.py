def ordinal(value):
    """
    Convert an integer to its ordinal as a string. 1 is '1st', 2 is '2nd',
    3 is '3rd', etc. Works for any non-negative integer.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    if value < 0:
        return str(value)
    if value == 1:
        # Translators: Ordinal format when value is 1 (1st).
        value = pgettext("ordinal is 1", "{}st").format(value)
    elif value % 100 in (11, 12, 13):
        # Translators: Ordinal format for 11 (11th), 12 (12th), and 13 (13th).
        value = pgettext("ordinal 11, 12, 13", "{}th").format(value)
    else:
        templates = (
            # Translators: Ordinal format when value ends with 0, e.g. 80th.
            pgettext("ordinal 0", "{}th"),
            # Translators: Ordinal format when value ends with 1, e.g. 81st,
            # except 11.
            pgettext("ordinal 1", "{}st"),
            # Translators: Ordinal format when value ends with 2, e.g. 82nd,
            # except 12.
            pgettext("ordinal 2", "{}nd"),
            # Translators: Ordinal format when value ends with 3, e.g. 83rd,
            # except 13.
            pgettext("ordinal 3", "{}rd"),
            # Translators: Ordinal format when value ends with 4, e.g. 84th.
            pgettext("ordinal 4", "{}th"),
            # Translators: Ordinal format when value ends with 5, e.g. 85th.
            pgettext("ordinal 5", "{}th"),
            # Translators: Ordinal format when value ends with 6, e.g. 86th.
            pgettext("ordinal 6", "{}th"),
            # Translators: Ordinal format when value ends with 7, e.g. 87th.
            pgettext("ordinal 7", "{}th"),
            # Translators: Ordinal format when value ends with 8, e.g. 88th.
            pgettext("ordinal 8", "{}th"),
            # Translators: Ordinal format when value ends with 9, e.g. 89th.
            pgettext("ordinal 9", "{}th"),
        )
        value = templates[value % 10].format(value)
    # Mark value safe so i18n does not break with <sup> or <sub> see #19988
    return mark_safe(value)
def make_style(config_string=""):
    """
    Create a Style object from the given config_string.

    If config_string is empty django.utils.termcolors.DEFAULT_PALETTE is used.
    """

    style = Style()

    color_settings = termcolors.parse_color_setting(config_string)

    # The nocolor palette has all available roles.
    # Use that palette as the basis for populating
    # the palette as defined in the environment.
    for role in termcolors.PALETTES[termcolors.NOCOLOR_PALETTE]:
        if color_settings:
            format = color_settings.get(role, {})
            style_func = termcolors.make_style(**format)
        else:

            def style_func(x):
                return x

        setattr(style, role, style_func)

    # For backwards compatibility,
    # set style for ERROR_OUTPUT == ERROR
    style.ERROR_OUTPUT = style.ERROR

    return style
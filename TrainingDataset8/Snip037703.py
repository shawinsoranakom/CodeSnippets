def _populate_theme_msg(msg: CustomThemeConfig) -> None:
    enum_encoded_options = {"base", "font"}
    theme_opts = config.get_options_for_section("theme")

    if not any(theme_opts.values()):
        return

    for option_name, option_val in theme_opts.items():
        if option_name not in enum_encoded_options and option_val is not None:
            setattr(msg, to_snake_case(option_name), option_val)

    # NOTE: If unset, base and font will default to the protobuf enum zero
    # values, which are BaseTheme.LIGHT and FontFamily.SANS_SERIF,
    # respectively. This is why we both don't handle the cases explicitly and
    # also only log a warning when receiving invalid base/font options.
    base_map = {
        "light": msg.BaseTheme.LIGHT,
        "dark": msg.BaseTheme.DARK,
    }
    base = theme_opts["base"]
    if base is not None:
        if base not in base_map:
            LOGGER.warning(
                f'"{base}" is an invalid value for theme.base.'
                f" Allowed values include {list(base_map.keys())}."
                ' Setting theme.base to "light".'
            )
        else:
            msg.base = base_map[base]

    font_map = {
        "sans serif": msg.FontFamily.SANS_SERIF,
        "serif": msg.FontFamily.SERIF,
        "monospace": msg.FontFamily.MONOSPACE,
    }
    font = theme_opts["font"]
    if font is not None:
        if font not in font_map:
            LOGGER.warning(
                f'"{font}" is an invalid value for theme.font.'
                f" Allowed values include {list(font_map.keys())}."
                ' Setting theme.font to "sans serif".'
            )
        else:
            msg.font = font_map[font]
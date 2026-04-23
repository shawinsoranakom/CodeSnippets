def get_clean_fonts() -> list[str]:
    """ Return a sane list of fonts for the system that has both regular and bold variants.

    Pre-pend "default" to the beginning of the list.

    Returns
    -------
    list[str]:
        A list of valid fonts for the system
    """
    f_manager = font_manager.FontManager()
    fonts: dict[str, dict[str, bool]] = {}
    for fnt in f_manager.ttflist:
        if str(fnt.weight) in ("400", "normal", "regular"):
            fonts.setdefault(fnt.name, {})["regular"] = True
        if str(fnt.weight) in ("700", "bold"):
            fonts.setdefault(fnt.name, {})["bold"] = True
    valid_fonts = {key for key, val in fonts.items() if len(val) == 2}
    retval = sorted(list(valid_fonts.intersection(tk_font.families())))
    if not retval:
        # Return the font list with any @prefixed or non-Unicode characters stripped and default
        # prefixed
        logger.debug("No bold/regular fonts found. Running simple filter")
        retval = sorted([fnt for fnt in tk_font.families()
                         if not fnt.startswith("@") and not any(ord(c) > 127 for c in fnt)])
    return ["default"] + retval
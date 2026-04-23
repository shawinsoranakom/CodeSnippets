def parse_color_setting(config_string):
    """Parse a DJANGO_COLORS environment variable to produce the system palette

    The general form of a palette definition is:

        "palette;role=fg;role=fg/bg;role=fg,option,option;role=fg/bg,option,option"

    where:
        palette is a named palette; one of 'light', 'dark', or 'nocolor'.
        role is a named style used by Django
        fg is a foreground color.
        bg is a background color.
        option is a display options.

    Specifying a named palette is the same as manually specifying the
    individual definitions for each role. Any individual definitions following
    the palette definition will augment the base palette definition.

    Valid roles:
        'error', 'success', 'warning', 'notice', 'sql_field', 'sql_coltype',
        'sql_keyword', 'sql_table', 'http_info', 'http_success',
        'http_redirect', 'http_not_modified', 'http_bad_request',
        'http_not_found', 'http_server_error', 'migrate_heading',
        'migrate_label'

    Valid colors:
        'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

    Valid options:
        'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'
    """
    if not config_string:
        return PALETTES[DEFAULT_PALETTE]

    # Split the color configuration into parts
    parts = config_string.lower().split(";")
    palette = PALETTES[NOCOLOR_PALETTE].copy()
    for part in parts:
        if part in PALETTES:
            # A default palette has been specified
            palette.update(PALETTES[part])
        elif "=" in part:
            # Process a palette defining string
            definition = {}

            # Break the definition into the role,
            # plus the list of specific instructions.
            # The role must be in upper case
            role, instructions = part.split("=")
            role = role.upper()

            styles = instructions.split(",")
            styles.reverse()

            # The first instruction can contain a slash
            # to break apart fg/bg.
            colors = styles.pop().split("/")
            colors.reverse()
            fg = colors.pop()
            if fg in color_names:
                definition["fg"] = fg
            if colors and colors[-1] in color_names:
                definition["bg"] = colors[-1]

            # All remaining instructions are options
            opts = tuple(s for s in styles if s in opt_dict)
            if opts:
                definition["opts"] = opts

            # The nocolor palette has all available roles.
            # Use that palette as the basis for determining
            # if the role is valid.
            if role in PALETTES[NOCOLOR_PALETTE] and definition:
                palette[role] = definition

    # If there are no colors specified, return the empty palette.
    if palette == PALETTES[NOCOLOR_PALETTE]:
        return None
    return palette
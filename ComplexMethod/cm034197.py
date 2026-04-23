def _format(string, *args):

    """ add ascii formatting or delimiters """

    for style in args:

        if style not in ref_style and style.upper() not in STYLE and style not in C.COLOR_CODES:
            raise KeyError("Invalid format value supplied: %s" % style)

        if C.ANSIBLE_NOCOLOR:
            # ignore most styles, but some already had 'identifier strings'
            if style in NOCOLOR:
                string = NOCOLOR[style] % string
        elif style in C.COLOR_CODES:
            string = stringc(string, style)
        elif style in ref_style:
            # assumes refs are also always colors
            string = stringc(string, ref_style[style])
        else:
            # start specific style and 'end' with normal
            string = '%s%s%s' % (STYLE[style.upper()], string, STYLE['NORMAL'])

    return string
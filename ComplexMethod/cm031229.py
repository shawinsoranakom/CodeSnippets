def _script_from_settings(settings):
    """Returns an appropriate script, based on settings, according to
    theme_settings definition to be used by theme_settings and
    theme_create."""
    script = []
    # a script will be generated according to settings passed, which
    # will then be evaluated by Tcl
    for name, opts in settings.items():
        # will format specific keys according to Tcl code
        if opts.get('configure'): # format 'configure'
            s = ' '.join(_format_optdict(opts['configure'], True))
            script.append("ttk::style configure %s %s;" % (name, s))

        if opts.get('map'): # format 'map'
            s = ' '.join(_format_mapdict(opts['map'], True))
            script.append("ttk::style map %s %s;" % (name, s))

        if 'layout' in opts: # format 'layout' which may be empty
            if not opts['layout']:
                s = 'null' # could be any other word, but this one makes sense
            else:
                s, _ = _format_layoutlist(opts['layout'])
            script.append("ttk::style layout %s {\n%s\n}" % (name, s))

        if opts.get('element create'): # format 'element create'
            eopts = opts['element create']
            etype = eopts[0]

            # find where args end, and where kwargs start
            argc = 1 # etype was the first one
            while argc < len(eopts) and not hasattr(eopts[argc], 'items'):
                argc += 1

            elemargs = eopts[1:argc]
            elemkw = eopts[argc] if argc < len(eopts) and eopts[argc] else {}
            specs, eopts = _format_elemcreate(etype, True, *elemargs, **elemkw)

            script.append("ttk::style element create %s %s %s %s" % (
                name, etype, specs, eopts))

    return '\n'.join(script)
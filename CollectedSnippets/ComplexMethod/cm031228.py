def _format_elemcreate(etype, script=False, *args, **kw):
    """Formats args and kw according to the given element factory etype."""
    specs = ()
    opts = ()
    if etype == "image": # define an element based on an image
        # first arg should be the default image name
        iname = args[0]
        # next args, if any, are statespec/value pairs which is almost
        # a mapdict, but we just need the value
        imagespec = (iname, *_mapdict_values(args[1:]))
        if script:
            specs = (imagespec,)
        else:
            specs = (_join(imagespec),)
        opts = _format_optdict(kw, script)

    if etype == "vsapi":
        # define an element whose visual appearance is drawn using the
        # Microsoft Visual Styles API which is responsible for the
        # themed styles on Windows XP and Vista.
        # Availability: Tk 8.6, Windows XP and Vista.
        if len(args) < 3:
            class_name, part_id = args
            statemap = (((), 1),)
        else:
            class_name, part_id, statemap = args
        specs = (class_name, part_id, tuple(_mapdict_values(statemap)))
        opts = _format_optdict(kw, script)

    elif etype == "from": # clone an element
        # it expects a themename and optionally an element to clone from,
        # otherwise it will clone {} (empty element)
        specs = (args[0],) # theme name
        if len(args) > 1: # elementfrom specified
            opts = (_format_optvalue(args[1], script),)

    if script:
        specs = _join(specs)
        opts = ' '.join(opts)
        return specs, opts
    else:
        return *specs, opts
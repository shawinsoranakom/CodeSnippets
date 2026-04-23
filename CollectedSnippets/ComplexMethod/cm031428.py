def _install_handlers(cp, formatters):
    """Install and return handlers"""
    hlist = cp["handlers"]["keys"]
    if not len(hlist):
        return {}
    hlist = hlist.split(",")
    hlist = _strip_spaces(hlist)
    handlers = {}
    fixups = [] #for inter-handler references
    for hand in hlist:
        section = cp["handler_%s" % hand]
        klass = section["class"]
        fmt = section.get("formatter", "")
        try:
            klass = eval(klass, vars(logging))
        except (AttributeError, NameError):
            klass = _resolve(klass)
        args = section.get("args", '()')
        args = eval(args, vars(logging))
        kwargs = section.get("kwargs", '{}')
        kwargs = eval(kwargs, vars(logging))
        h = klass(*args, **kwargs)
        h.name = hand
        if "level" in section:
            level = section["level"]
            h.setLevel(level)
        if len(fmt):
            h.setFormatter(formatters[fmt])
        if issubclass(klass, logging.handlers.MemoryHandler):
            target = section.get("target", "")
            if len(target): #the target handler may not be loaded yet, so keep for later...
                fixups.append((h, target))
        handlers[hand] = h
    #now all handlers are loaded, fixup inter-handler references...
    for h, t in fixups:
        h.setTarget(handlers[t])
    return handlers
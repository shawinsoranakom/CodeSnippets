def _install_loggers(cp, handlers, disable_existing):
    """Create and install loggers"""

    # configure the root first
    llist = cp["loggers"]["keys"]
    llist = llist.split(",")
    llist = list(_strip_spaces(llist))
    llist.remove("root")
    section = cp["logger_root"]
    root = logging.root
    log = root
    if "level" in section:
        level = section["level"]
        log.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)
    hlist = section["handlers"]
    if len(hlist):
        hlist = hlist.split(",")
        hlist = _strip_spaces(hlist)
        for hand in hlist:
            log.addHandler(handlers[hand])

    #and now the others...
    #we don't want to lose the existing loggers,
    #since other threads may have pointers to them.
    #existing is set to contain all existing loggers,
    #and as we go through the new configuration we
    #remove any which are configured. At the end,
    #what's left in existing is the set of loggers
    #which were in the previous configuration but
    #which are not in the new configuration.
    existing = list(root.manager.loggerDict.keys())
    #The list needs to be sorted so that we can
    #avoid disabling child loggers of explicitly
    #named loggers. With a sorted list it is easier
    #to find the child loggers.
    existing.sort()
    #We'll keep the list of existing loggers
    #which are children of named loggers here...
    child_loggers = []
    #now set up the new ones...
    for log in llist:
        section = cp["logger_%s" % log]
        qn = section["qualname"]
        propagate = section.getint("propagate", fallback=1)
        logger = logging.getLogger(qn)
        if qn in existing:
            i = existing.index(qn) + 1 # start with the entry after qn
            prefixed = qn + "."
            pflen = len(prefixed)
            num_existing = len(existing)
            while i < num_existing:
                if existing[i][:pflen] == prefixed:
                    child_loggers.append(existing[i])
                i += 1
            existing.remove(qn)
        if "level" in section:
            level = section["level"]
            logger.setLevel(level)
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.propagate = propagate
        logger.disabled = 0
        hlist = section["handlers"]
        if len(hlist):
            hlist = hlist.split(",")
            hlist = _strip_spaces(hlist)
            for hand in hlist:
                logger.addHandler(handlers[hand])

    #Disable any old loggers. There's no point deleting
    #them as other threads may continue to hold references
    #and by disabling them, you stop them doing any logging.
    #However, don't disable children of named loggers, as that's
    #probably not what was intended by the user.
    #for log in existing:
    #    logger = root.manager.loggerDict[log]
    #    if log in child_loggers:
    #        logger.level = logging.NOTSET
    #        logger.handlers = []
    #        logger.propagate = 1
    #    elif disable_existing_loggers:
    #        logger.disabled = 1
    _handle_existing_loggers(existing, child_loggers, disable_existing)
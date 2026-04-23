def warn_explicit(message, category, filename, lineno,
                  module=None, registry=None, module_globals=None,
                  source=None):
    lineno = int(lineno)
    if isinstance(message, Warning):
        text = str(message)
        category = message.__class__
    else:
        text = message
        message = category(message)
    key = (text, category, lineno)
    with _wm._lock:
        if registry is None:
            registry = {}
        if registry.get('version', 0) != _wm._filters_version:
            registry.clear()
            registry['version'] = _wm._filters_version
        # Quick test for common case
        if registry.get(key):
            return
        # Search the filters
        for item in _wm._get_filters():
            action, msg, cat, mod, ln = item
            if ((msg is None or msg.match(text)) and
                issubclass(category, cat) and
                (ln == 0 or lineno == ln) and
                (mod is None or (_match_filename(mod, filename)
                                 if module is None else
                                 mod.match(module)))):
                    break
        else:
            action = _wm.defaultaction
        # Early exit actions
        if action == "ignore":
            return

        if action == "error":
            raise message
        # Other actions
        if action == "once":
            registry[key] = 1
            oncekey = (text, category)
            if _wm.onceregistry.get(oncekey):
                return
            _wm.onceregistry[oncekey] = 1
        elif action in {"always", "all"}:
            pass
        elif action == "module":
            registry[key] = 1
            altkey = (text, category, 0)
            if registry.get(altkey):
                return
            registry[altkey] = 1
        elif action == "default":
            registry[key] = 1
        else:
            # Unrecognized actions are errors
            raise RuntimeError(
                  "Unrecognized action (%r) in warnings.filters:\n %s" %
                  (action, item))

    # Prime the linecache for formatting, in case the
    # "file" is actually in a zipfile or something.
    import linecache
    linecache.getlines(filename, module_globals)

    # Print message and context
    msg = _wm.WarningMessage(message, category, filename, lineno, source=source)
    _wm._showwarnmsg(msg)
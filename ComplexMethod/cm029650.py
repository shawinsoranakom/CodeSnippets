def warn(message, category=None, stacklevel=1, source=None,
         *, skip_file_prefixes=()):
    """Issue a warning, or maybe ignore it or raise an exception."""
    # Check if message is already a Warning object
    if isinstance(message, Warning):
        category = message.__class__
    # Check category argument
    if category is None:
        category = UserWarning
    elif not isinstance(category, type):
        raise TypeError(f"category must be a Warning subclass, not "
                        f"'{type(category).__name__}'")
    elif not issubclass(category, Warning):
        raise TypeError(f"category must be a Warning subclass, not "
                        f"class '{category.__name__}'")
    if not isinstance(skip_file_prefixes, tuple):
        # The C version demands a tuple for implementation performance.
        raise TypeError('skip_file_prefixes must be a tuple of strs.')
    if skip_file_prefixes:
        stacklevel = max(2, stacklevel)
    # Get context information
    try:
        if stacklevel <= 1 or _is_internal_frame(sys._getframe(1)):
            # If frame is too small to care or if the warning originated in
            # internal code, then do not try to hide any frames.
            frame = sys._getframe(stacklevel)
        else:
            frame = sys._getframe(1)
            # Look for one frame less since the above line starts us off.
            for x in range(stacklevel-1):
                frame = _next_external_frame(frame, skip_file_prefixes)
                if frame is None:
                    raise ValueError
    except ValueError:
        globals = sys.__dict__
        filename = "<sys>"
        lineno = 0
    else:
        globals = frame.f_globals
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
    if '__name__' in globals:
        module = globals['__name__']
    else:
        module = "<string>"
    registry = globals.setdefault("__warningregistry__", {})
    _wm.warn_explicit(
        message,
        category,
        filename,
        lineno,
        module,
        registry,
        globals,
        source=source,
    )
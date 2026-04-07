def _restore_context(context):
    """
    Check for changes in contextvars, and set them to the current
    context for downstream consumers.
    """
    for cvar in context:
        cvalue = context.get(cvar)
        try:
            if cvar.get() != cvalue:
                cvar.set(cvalue)
        except LookupError:
            cvar.set(cvalue)
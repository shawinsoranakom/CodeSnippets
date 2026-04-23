def __getattr__(name):
    try:
        msg = _deprecate_on_import[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    else:
        # Issue deprecation warnings at time of import.
        from django.core.mail import message

        warnings.warn(msg, category=RemovedInDjango70Warning)
        return getattr(message, name)
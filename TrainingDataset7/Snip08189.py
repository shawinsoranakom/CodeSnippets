def _get_dynamic_attr(self, attname, obj, default=None):
        try:
            attr = getattr(self, attname)
        except AttributeError:
            return default
        if callable(attr):
            # Check co_argcount rather than try/excepting the function and
            # catching the TypeError, because something inside the function
            # may raise the TypeError. This technique is more accurate.
            func = unwrap(attr)
            try:
                code = func.__code__
            except AttributeError:
                func = unwrap(attr.__call__)
                code = func.__code__
            # If function doesn't have arguments and it is not a static method,
            # it was decorated without using @functools.wraps.
            if not code.co_argcount and not isinstance(
                getattr_static(self, func.__name__, None), staticmethod
            ):
                raise ImproperlyConfigured(
                    f"Feed method {attname!r} decorated by {func.__name__!r} needs to "
                    f"use @functools.wraps."
                )
            if code.co_argcount == 2:  # one argument is 'self'
                return attr(obj)
            else:
                return attr()
        return attr
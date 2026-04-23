def no_type_check(arg):
    """Decorator to indicate that annotations are not type hints.

    The argument must be a class or function; if it is a class, it
    applies recursively to all methods and classes defined in that class
    (but not to methods defined in its superclasses or subclasses).

    This mutates the function(s) or class(es) in place.
    """
    if isinstance(arg, type):
        for key in dir(arg):
            obj = getattr(arg, key)
            if (
                not hasattr(obj, '__qualname__')
                or obj.__qualname__ != f'{arg.__qualname__}.{obj.__name__}'
                or getattr(obj, '__module__', None) != arg.__module__
            ):
                # We only modify objects that are defined in this type directly.
                # If classes / methods are nested in multiple layers,
                # we will modify them when processing their direct holders.
                continue
            # Instance, class, and static methods:
            if isinstance(obj, types.FunctionType):
                obj.__no_type_check__ = True
            if isinstance(obj, types.MethodType):
                obj.__func__.__no_type_check__ = True
            # Nested types:
            if isinstance(obj, type):
                no_type_check(obj)
    try:
        arg.__no_type_check__ = True
    except TypeError:  # built-in classes
        pass
    return arg
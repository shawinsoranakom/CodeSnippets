def visiblename(name, all=None, obj=None):
    """Decide whether to show documentation on a variable."""
    # Certain special names are redundant or internal.
    # XXX Remove __initializing__?
    if name in {'__author__', '__builtins__', '__credits__', '__date__',
                '__doc__', '__file__', '__spec__', '__loader__', '__module__',
                '__name__', '__package__', '__path__', '__qualname__',
                '__slots__', '__version__', '__static_attributes__',
                '__firstlineno__', '__annotate_func__',
                '__annotations_cache__'}:
        return 0
    # Private names are hidden, but special names are displayed.
    if name.startswith('__') and name.endswith('__'): return 1
    # Namedtuples have public fields and methods with a single leading underscore
    if name.startswith('_') and hasattr(obj, '_fields'):
        return True
    # Ignore __future__ imports.
    if obj is not __future__ and name in _future_feature_names:
        if isinstance(getattr(obj, name, None), __future__._Feature):
            return False
    if all is not None:
        # only document that which the programmer exported in __all__
        return name in all
    else:
        return not name.startswith('_')
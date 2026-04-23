def createResolutionCallbackForClassMethods(cls: type) -> Callable[[str], Any]:
    """
    This looks at all the methods defined in a class and pulls their closed-over
    variables into a dictionary and uses that to resolve variables.
    """
    # cls is a type here, so `ismethod` is false since the methods on the type
    # aren't bound to anything, so Python treats them as regular functions
    fns = [
        getattr(cls, name)
        for name in cls.__dict__
        if inspect.isroutine(getattr(cls, name))
    ]
    # Skip built-ins, as they do not have global scope nor type hints
    # Needed to support `enum.Enum` derived classes in Python-3.11
    # That adds `_new_member_` property which is an alias to `__new__`
    # Skip __annotate__ added by PEP 649 for deferred annotation evaluation
    fns = [
        fn
        for fn in fns
        if not inspect.isbuiltin(fn)
        and hasattr(fn, "__globals__")
        and fn.__name__ != "__annotate__"
    ]
    captures = {}

    for fn in fns:
        captures.update(get_closure(fn))
        captures.update(get_type_hint_captures(fn))

    def lookup_in_class(key: str) -> Any:
        if key in captures:
            return captures[key]
        else:
            return getattr(builtins, key, None)

    return lookup_in_class
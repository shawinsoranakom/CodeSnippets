def wrap_type(to_patch: Any, pattern: type, __torch_function__: Callable) -> None:
    wrap_method = _py_wrap_method

    all: dict[str, Any] = {}
    for t in reversed(pattern.mro()[:-1]):  # skip object
        all.update(t.__dict__)

    def wrap_attr(orig: Any) -> property:
        return property(wrap_method(orig.__get__, __torch_function__))

    for name, obj in all.items():
        if name in (
            "__dict__",
            "__new__",
            "__init__",
            "__repr__",
            "__weakref__",
            "__doc__",
            "__module__",
            "__dir__",
        ):
            continue

        # skip things that have been overloaded
        # things that come from object like `__eq__` still need to be patched, however.
        if hasattr(to_patch, name) and getattr(to_patch, name) is not getattr(
            object, name, None
        ):
            continue

        if isinstance(obj, FUNC_TYPES):
            setattr(to_patch, name, wrap_method(obj, __torch_function__))
        elif isinstance(obj, PROPERTY_TYPES):
            setattr(to_patch, name, wrap_attr(obj))
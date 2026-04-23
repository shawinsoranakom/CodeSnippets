def whichmodule(obj, name):
    """Find the module an object belong to."""
    dotted_path = name.split('.')
    module_name = getattr(obj, '__module__', None)
    if '<locals>' in dotted_path:
        raise PicklingError(f"Can't pickle local object {obj!r}")
    if module_name is None:
        # Protect the iteration by using a list copy of sys.modules against dynamic
        # modules that trigger imports of other modules upon calls to getattr.
        for module_name, module in sys.modules.copy().items():
            if (module_name == '__main__'
                or module_name == '__mp_main__'  # bpo-42406
                or module is None):
                continue
            try:
                if _getattribute(module, dotted_path) is obj:
                    return module_name
            except AttributeError:
                pass
        module_name = '__main__'

    try:
        __import__(module_name, level=0)
        module = sys.modules[module_name]
    except (ImportError, ValueError, KeyError) as exc:
        raise PicklingError(f"Can't pickle {obj!r}: {exc!s}")
    try:
        if _getattribute(module, dotted_path) is obj:
            return module_name
    except AttributeError:
        raise PicklingError(f"Can't pickle {obj!r}: "
                            f"it's not found as {module_name}.{name}")

    raise PicklingError(
        f"Can't pickle {obj!r}: it's not the same object as {module_name}.{name}")
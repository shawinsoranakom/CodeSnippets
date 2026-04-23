def get_torch_modules(obj: T.Any,  # noqa[C901]  # pylint:disable=too-many-branches,too-many-return-statements
                      mod: str | None = None,
                      seen: set[int] | None = None,
                      results: list[torch.nn.Module] | None = None) -> list[torch.nn.Module]:
    """Recursively search a plugin's model attribute to find any parent :class:`torch.nn.Module`s

    Parameters
    ----------
    obj
        The object to check if it is a torch Module. This should be a plugin's `model` attribute
    mod
        The module that the parent model class belongs to. Default: ``None`` (Collected from the
        first object entered into the recursive function)
    seen
        A set of seen object IDs to prevent self-recursion. Default: ``None`` (Created when the
        first object enters the recursive function)
    results
        List of discovered torch modules. Default: ``None`` (Created when the first object enters
        the recursive function)

    Returns
    -------
    The list of discovered torch Modules
    """
    seen = set() if seen is None else seen
    retval: list[torch.nn.Module] = [] if results is None else results
    mod = obj.__class__.__module__ if mod is None else mod

    obj_id = id(obj)
    if obj_id in seen:
        return retval
    seen.add(obj_id)

    if isinstance(obj, torch.nn.Module):
        logger.debug("Torch module found in %s(%s)", obj.__class__.__name__, type(obj))
        retval.append(obj)
        return retval

    if isinstance(obj, (str, bytes, int, float, bool, type(None))):
        # Fast exit on primitive
        return retval

    if hasattr(obj, "__class__") and obj.__class__.__module__ not in (mod, "builtins"):
        # Never leave the plugin module
        return retval

    if isinstance(obj, Mapping):
        # Mapping before iterable as a mapping is also an iterable
        for v in obj.values():
            retval = get_torch_modules(v, mod, seen=seen, results=retval)

    if isinstance(obj, Iterable):
        for v in obj:
            retval = get_torch_modules(v, mod, seen=seen, results=retval)

    if hasattr(obj, "__dict__"):
        for v in obj.__dict__.values():
            retval = get_torch_modules(v, mod, seen=seen, results=retval)
    return retval
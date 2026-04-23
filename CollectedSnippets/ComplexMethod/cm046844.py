def _resolve_trainer_params(trainer_class, init_fn):
    """Resolve the real named parameters for a trainer __init__.

    Some TRL trainers (e.g., ORPOTrainer in TRL 0.27.1) are thin wrappers
    with only ``def __init__(self, *args, **kwargs)``.  For those, walk the
    MRO and return the first parent class that has real named parameters.
    """
    params = inspect.signature(init_fn).parameters
    named = {
        k
        for k, v in params.items()
        if v.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        and k != "self"
    }
    if named:
        return set(params.keys())

    # Thin wrapper detected - walk MRO for real signature
    for cls in trainer_class.__mro__[1:]:
        if cls is object:
            continue
        parent_init = cls.__dict__.get("__init__")
        if parent_init is None:
            continue
        try:
            parent_params = inspect.signature(parent_init).parameters
            parent_named = {
                k
                for k, v in parent_params.items()
                if v.kind
                in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
                and k != "self"
            }
            if parent_named:
                return set(parent_params.keys())
        except (ValueError, TypeError):
            continue
    return set(params.keys())
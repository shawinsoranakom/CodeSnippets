def check_parameter(pparam: inspect.Parameter, cparam: inspect.Parameter, is_private: bool = False) -> bool:
    # don't check annotations
    return (
        pparam.name == cparam.name
        or pparam.kind == POSITIONAL_ONLY
        or is_private  # ignore names of (positional or keyword) attributes
    ) and (
        # if parent has a default, child should have the same one
        pparam.default is EMPTY
        or pparam.default == cparam.default
    ) and (
        # if both are annotated, then they should be similar (for typing)
        (pann := pparam.annotation) is EMPTY
        or (cann := cparam.annotation) is EMPTY
        or pann == cann
        # accept annotations of different types as valid to keep logic simple
        # for example, typing can be a str or the class
        or pann.__class__ != cann.__class__
    )
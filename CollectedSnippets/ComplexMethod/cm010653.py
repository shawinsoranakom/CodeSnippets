def synthesize__init__(cls) -> ParsedDef:
    # Supporting default factories in the way that people expect would sort of require us to
    # allow compiling lambda functions, which is not currently supported.
    if any(
        field.default_factory is not dataclasses.MISSING
        for field in dataclasses.fields(cls)
    ):
        raise NotImplementedError(
            "Default factory initializers are not supported in TorchScript dataclasses"
        )

    # Simply read off the generated __init__ signature from CPython's implementation. It'll be
    # almost correct except for InitVar annotations, which we need to handle specially.
    signature = inspect.signature(cls.__init__)

    # Handle InitVars if needed (only works on Python 3.8+, when a `type` attribute was added to InitVar);
    # see CPython commit here https://github.com/python/cpython/commit/01ee12ba35a333e8a6a25c4153c4a21838e9585c
    init_vars: list[str] = []
    params = []
    for name, param in signature.parameters.items():
        ann = param.annotation

        if isinstance(ann, dataclasses.InitVar):
            # The TorchScript interpreter can't handle InitVar annotations, so we unwrap the underlying type here
            init_vars.append(name)
            params.append(param.replace(annotation=ann.type))  # type: ignore[attr-defined]
        else:
            params.append(param)

    signature = signature.replace(parameters=params)

    body = [
        # Assign all attributes to self
        f"self.{field.name} = {field.name}"
        for field in dataclasses.fields(cls)
        if field.init and field.name not in init_vars
    ]
    # Call user's impl of __post_init__ if it exists
    if hasattr(cls, "__post_init__"):
        body.append("self.__post_init__(" + ", ".join(init_vars) + ")")

    return compose_fn(cls, "__init__", body or ["pass"], signature=str(signature))
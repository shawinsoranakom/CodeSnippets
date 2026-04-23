def get_field(cls: ConfigType, name: str) -> Any:
    """Get the default factory field of a dataclass by name. Used for getting
    default factory fields in `EngineArgs`."""
    if not is_dataclass(cls):
        raise TypeError("The given class is not a dataclass.")
    try:
        named_field = next(f for f in fields(cls) if f.name == name)
    except StopIteration as e:
        raise ValueError(f"Field '{name}' not found in {cls.__name__}.") from e

    # The arguments to copy to the new field
    default = named_field.default
    default_factory = named_field.default_factory
    init = named_field.init

    # Handle pydantic.Field
    if isinstance(default, FieldInfo):
        if default.init is not None:
            init = default.init
        if default.default_factory is not None:
            default_factory = cast(Callable[[], Any], default.default_factory)
            default = MISSING
        else:
            default = default.default

    if default is MISSING and default_factory is MISSING:
        logger.warning_once(
            "%s.%s has no default or default factory.", cls.__name__, name
        )
    return field(default=default, default_factory=default_factory, init=init)
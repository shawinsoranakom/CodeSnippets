def namedtuple_fields(cls: type) -> tuple[str, ...]:
    """Get the fields of a namedtuple or a torch.return_types.* quasi-namedtuple"""
    if cls is slice:
        return ("start", "stop", "step")

    assert issubclass(cls, tuple)
    if hasattr(cls, "_fields"):
        # normal namedtuples
        return cls._fields

    @dataclasses.dataclass
    class Marker:
        index: int

    # frustrating ones e.g. torch.return_types.max
    assert cls.__module__ == "torch.return_types"
    obj = cls(map(Marker, range(cls.n_fields)))  # type: ignore[attr-defined]
    fields: dict[str, int] = {}
    for name in dir(obj):
        if name[0] != "_" and isinstance(getattr(obj, name), Marker):
            fields[name] = getattr(obj, name).index
    assert len(fields) == cls.n_fields  # type: ignore[attr-defined]
    return tuple(sorted(fields, key=fields.get))
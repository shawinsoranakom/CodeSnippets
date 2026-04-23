def impl_MATCH_CLASS(
    subject: object, cls: type, nargs: int, kwargs: tuple[str, ...]
) -> tuple[object, ...] | None:
    if not isinstance(cls, type):
        raise TypeError("called match pattern must be a class")

    if not isinstance(subject, cls):
        return None

    typ = type(subject)
    match_self = False
    match_args = ()

    attrs = []
    seen = set()

    if nargs:
        if hasattr(typ, "__match_args__"):
            match_args = typ.__match_args__

            if not isinstance(match_args, tuple):
                raise TypeError(
                    f"{typ}.__match_args__ must be a tuple, (got {type(match_args)})"
                )

            for name in match_args[:nargs]:
                if not isinstance(name, str):
                    raise TypeError(
                        f"__match_args__ elements must be strings (got {type(name)})"
                    )
                attrs.append(_match_class_attr(subject, name, seen))
        else:
            # We should somehow check if the type has TPFLAGS_MATCH_SELF set
            # match_self is only true if TPFLAGS_MATCH_SELF is set, but there is
            # no way to check for it directly in Python. So we assume it is set
            # if there are no __match_args__
            match_self = True
            attrs.append(subject)

        allowed = 1 if match_self else len(match_args)
        if allowed < nargs:
            raise TypeError(
                f"accepts {allowed} positional sub-patterns ({nargs} given)"
            )

    for name in kwargs:
        attrs.append(_match_class_attr(subject, name, seen))

    return tuple(attrs)
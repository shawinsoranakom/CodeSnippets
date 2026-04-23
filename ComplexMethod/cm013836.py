def is_namedtuple_cls(cls: Any) -> bool:
    """Test if an object is a namedtuple or a (torch.return_types|torch.autograd.forward_ad).* quasi-namedtuple"""
    try:
        if issubclass(cls, tuple):
            module = getattr(cls, "__module__", None)
            if module in ("torch.return_types", "torch.autograd.forward_ad"):
                return True
            if isinstance(getattr(cls, "_fields", None), tuple) and callable(
                getattr(cls, "_make", None)
            ):
                # The subclassing style namedtuple can have an extra base `typing.Generic`
                bases = tuple(t for t in cls.__bases__ if t is not Generic)
                if bases == (tuple,):
                    # This is a namedtuple type directly created by `collections.namedtuple(...)`
                    return True
                if bases and any(
                    (
                        # Subclass of namedtuple
                        is_namedtuple_cls(t)
                        # For subclasses of namedtuple, the __new__ method should not be customized
                        and cls.__new__ is t.__new__
                    )
                    for t in bases
                ):
                    return True
    except TypeError:
        pass
    return False
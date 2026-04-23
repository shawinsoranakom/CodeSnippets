def is_fun(t: object) -> TypeGuard[FunctionalTensor | Tensor]:
    if isinstance(t, Tensor) and is_traceable_wrapper_subclass(t):
        # See Note [Functionalization always runs last]
        # This means that if we want to "functionalize" a subclass, we need to ensure that the functional wrapper
        # goes at the bottom.
        # recurse here, so we can support nested wrapper subclasses
        t_attrs, _ = t.__tensor_flatten__()  # type: ignore[attr-defined]
        got_fun: bool | None = None
        for attr in t_attrs:
            match getattr(t, attr):
                case Tensor() as v:
                    fun = is_fun(v)
                    if got_fun is None:
                        got_fun = fun
                    elif got_fun != fun:
                        raise AssertionError(
                            "mixed functional/non-functional inner tensors"
                        )
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )
        return got_fun or False

    return isinstance(t, FunctionalTensor)
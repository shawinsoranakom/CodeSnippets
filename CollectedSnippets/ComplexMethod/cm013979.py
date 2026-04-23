def _get_frame(
    mod: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
) -> FrameInfo:
    """
    Create a frame to trace, given a model, args, and optional kwargs.
    """
    import builtins

    fn, self_opt = get_traced_fn(mod)
    if self_opt is not None:
        args = (self_opt,) + args
    if kwargs is None:
        kwargs = {}

    signature = _get_signature(fn)
    bound_arguments = signature.bind(*args, **kwargs)
    bound_arguments.apply_defaults()
    f_locals = bound_arguments.arguments

    closure = fn.__closure__ or ()
    freevars = fn.__code__.co_freevars
    if freevars or closure:
        assert len(closure) == len(freevars)
        f_locals.update(
            {name: cell.cell_contents for name, cell in zip(freevars, closure)}
        )

    return FrameInfo(
        fn.__code__,
        fn.__globals__,
        f_locals,
        builtins.__dict__,
        closure=fn.__closure__ or (),  # type: ignore[arg-type]
        argdefs=fn.__defaults__,
        kwdefaults=fn.__kwdefaults__,
    )
def wrapper(
        *args: Array | complex | None, **kwargs: Any
    ) -> tuple[Array, ...]:  # numpydoc ignore=GL08
        args_list = []
        device = None
        for arg in args:
            if arg is not None and not is_python_scalar(arg):
                if device is None:
                    device = _compat.device(arg)
                if as_numpy:
                    import numpy as np

                    arg = cast(Array, np.asarray(arg))  # pyright: ignore[reportInvalidCast] # noqa: PLW2901
            args_list.append(arg)
        assert device is not None

        out = func(*args_list, **kwargs)

        if multi_output:
            assert isinstance(out, Sequence)
            return tuple(xp.asarray(o, device=device) for o in out)
        return (xp.asarray(out, device=device),)
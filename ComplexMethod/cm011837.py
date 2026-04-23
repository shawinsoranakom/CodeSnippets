def wrapped(*args, **kwargs):
        args: list[Any] = list(args)
        kwargs: dict[str, Any] = dict(kwargs)
        unpacked = False
        # TODO maybe we need to use pytrees here
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            unpacked = True
            args = list(args[0])

        if not all(
            (fn in fallbacks or in_namespace(fn, "_c10d_functional")) for fn in aten_fn
        ):
            # explicitly assert for "out=" ops for better error messages
            assert not any(x == "out" for x in kwargs), "out= ops aren't yet supported"

        args, kwargs = transform_args(
            args, kwargs, broadcast, type_promotion_kind, convert_input_to_bool
        )

        if unpacked:
            args = [args]

        out = decomp_fn(*args, **kwargs)
        validate_ir(out)

        return out
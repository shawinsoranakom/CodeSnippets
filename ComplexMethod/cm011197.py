def __torch_dispatch__(  # type: ignore[override]
        cls,
        func: Any,
        types: tuple[Any, ...],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if kwargs is None:
            kwargs = {}

        # This is horribly inefficient
        flat_args, args_spec = pytree.tree_flatten((args, kwargs))
        local_tensor = None
        for arg in flat_args:
            if isinstance(arg, LocalTensor):
                local_tensor = arg
                break

        if local_tensor is None:
            raise AssertionError("At least one of the arguments must be a LocalTensor")

        # Check for unrecognized tensor subclasses (but allow regular tensors and scalars)
        has_unrecognized_types = _check_for_subclass(flat_args)
        if has_unrecognized_types:
            unrecognized_types = [
                type(x) for x in flat_args if _check_for_subclass_arg(x)
            ]
            not_implemented_log.debug(
                "LocalTensor unrecognized subclass(es): %s", unrecognized_types
            )
            return NotImplemented

        with LocalTensorMode(local_tensor._ranks):
            return func(*args, **kwargs)
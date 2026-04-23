def __torch_dispatch__(
        self,
        func: OpOverload,
        types: Any,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if not kwargs:
            kwargs = {}

        flat_tensor_args = filter(
            lambda x: isinstance(x, torch.Tensor), tree_flatten((args, kwargs))[0]
        )

        # Defer this to subclass torchdispatch modes (probably shouldn't have fake tensor here tho)
        # For Parameters, we need to check the underlying tensor type, not the Parameter itself
        for tensor in flat_tensor_args:
            underlying_tensor = tensor
            if isinstance(tensor, torch.nn.Parameter):
                underlying_tensor = tensor.data
            if type(underlying_tensor) not in HANDLED_TYPES:
                return NotImplemented

        res = func(*args, **kwargs)
        # Only check aliasing for custom ops (non-aten/prim/prims/_c10d_functional/c10d)
        # that claim to be functional
        # Skip ops whose schema declares aliasing is allowed
        if (
            not isinstance(func, torch._ops.HigherOrderOperator)
            and not is_builtin(func)
            # TODO (https://github.com/pytorch/pytorch/issues/170986)
            and func.namespace not in ("_c10d_functional", "c10d", "onednn")
            # This op is quite important but has wrong schema, so lets skip for now
            and not _is_fsdp_all_gather_copy_in(func)
            and not _schema_allows_aliasing(func)
        ):
            _check_custom_op_aliasing(
                func.name(),
                args,
                kwargs,
                res,
            )
        return res
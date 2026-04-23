def _mark_dynamic_inputs(
        mod: type[_T], ds_type: DynamicShapesType, *args: Any, **kwargs: Any
    ) -> None:
        def mark_dynamic(arg: torch.Tensor, dims: list[int]) -> None:
            if ds_type == DynamicShapesType.UNBACKED:
                if is_torch_equal_or_newer("2.10.0"):
                    for dim in dims:
                        torch._dynamo.decorators.mark_unbacked(
                            arg, dim, hint_override=arg.size()[dim]
                        )
                else:
                    torch._dynamo.decorators.mark_unbacked(arg, dims)
            else:
                torch._dynamo.mark_dynamic(arg, dims)

        sig = inspect.signature(mod.__class__.forward)  # type: ignore[attr-defined]
        bound_args = sig.bind(mod, *args, **kwargs)
        bound_args.apply_defaults()
        for k, dims in dynamic_arg_dims.items():
            arg = bound_args.arguments.get(k)

            if arg is not None:
                dims = [dims] if isinstance(dims, int) else dims
                if isinstance(arg, torch.Tensor):
                    # In case dims is specified with negative indexing
                    dims = [arg.ndim + dim if dim < 0 else dim for dim in dims]
                    mark_dynamic(arg, dims)
                elif isinstance(arg, IntermediateTensors):
                    for tensor in arg.tensors.values():
                        # In case dims is specified with negative indexing
                        dims = [tensor.ndim + dim if dim < 0 else dim for dim in dims]
                        mark_dynamic(tensor, dims)
                else:
                    raise ValueError(
                        "Unsupported dynamic dimensions"
                        f" {dims} for argument {k} with type {type(arg)}."
                    )
        if mark_unbacked_dims:
            for k, dims in mark_unbacked_dims.items():
                arg = bound_args.arguments.get(k)
                if arg is not None:
                    dims = [dims] if isinstance(dims, int) else dims
                    if isinstance(arg, torch.Tensor):
                        # In case dims is specified with negative indexing
                        dims = [arg.ndim + dim if dim < 0 else dim for dim in dims]
                        if is_torch_equal_or_newer("2.10.0"):
                            for dim in dims:
                                torch._dynamo.decorators.mark_unbacked(
                                    arg, dim, hint_override=arg.size()[dim]
                                )
                        else:
                            torch._dynamo.decorators.mark_unbacked(arg, dims)
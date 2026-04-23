def _unwrap_to_op_info_impl(
        self,
        op_call: torch._ops.OpOverload,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        create_schema: bool,
    ) -> OpInfo:
        # get runtime schema info to determine whether to use pytree to flatten inputs
        runtime_schema_info = self.sharding_propagator.op_to_schema_info.get(
            op_call, None
        )
        if runtime_schema_info is None:
            runtime_schema_info = (
                self.sharding_propagator.op_to_schema_info_for_single_dim_strategy.get(
                    op_call, None
                )
            )

        # Auto-detect needs_pytree if any arg is a list/tuple containing tensors
        def _contains_tensor(arg: object) -> bool:
            if isinstance(arg, (list, tuple)):
                return any(isinstance(item, torch.Tensor) for item in arg)
            return False

        needs_pytree = (
            runtime_schema_info is not None and runtime_schema_info.needs_pytree
        ) or any(_contains_tensor(arg) for arg in args)

        if needs_pytree:
            # flatten args/kwargs when op says necessary or args contain lists/tuples
            tree_args, args_spec = pytree.tree_flatten(args)
            args_list: Sequence[object] = tree_args
        else:
            args_list, args_spec = args, None

        args_schema: list[object] = []
        kwargs_schema: dict[str, object] = {}
        local_args: list[object] = []
        local_kwargs: dict[str, object] = {}
        compute_mesh: DeviceMesh | None = None

        for arg in args_list:
            if isinstance(arg, dtensor.DTensor):
                local_args.append(arg._local_tensor)
                args_schema.append(arg._spec)
                if compute_mesh is None:
                    # record the first compute device mesh from args
                    compute_mesh = arg.device_mesh
            elif isinstance(arg, torch.Tensor):
                compute_mesh = compute_mesh or try_find_mesh_from_args(
                    op_call, args_list
                )
                args_schema.append(
                    self._try_replicate_spec_for_scalar_tensor(
                        op_call, arg, compute_mesh
                    )
                )
                local_args.append(arg)
            else:
                # non DTensor/Tensor args (i.e. int/float/bool), just add to args_schema/local_args
                args_schema.append(arg)
                local_args.append(arg)

        for k, v in kwargs.items():
            if isinstance(v, dtensor.DTensor):
                local_kwargs[k] = v._local_tensor
                kwargs_schema[k] = v._spec
                if compute_mesh is None:
                    # record the first compute device mesh from kwargs
                    compute_mesh = v.device_mesh
            elif isinstance(v, torch.Tensor):
                compute_mesh = compute_mesh or try_find_mesh_from_args(
                    op_call, args_list
                )
                kwargs_schema[k] = self._try_replicate_spec_for_scalar_tensor(
                    op_call,
                    v,
                    compute_mesh,
                )
                local_kwargs[k] = v
            else:
                # non DTensor/Tensor args (i.e. int/float/bool), just add to args_schema/local_args
                kwargs_schema[k] = v
                local_kwargs[k] = v

        if compute_mesh is None:
            raise AssertionError(
                f"found no DeviceMesh from dtensor args for {op_call}!"
            )
        op_info = OpInfo(
            compute_mesh,
            OpSchema(
                op_call,
                (
                    # pyrefly: ignore [bad-argument-type]
                    pytree.tree_unflatten(args_schema, args_spec)
                    if args_spec
                    else tuple(args_schema)
                ),
                kwargs_schema,
                schema_info=runtime_schema_info,
            )
            if create_schema
            else None,  # type: ignore[arg-type]
            args_schema,
            tuple(local_args),
            local_kwargs,
            args_spec,
        )
        return op_info
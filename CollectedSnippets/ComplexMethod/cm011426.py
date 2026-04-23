def _dispatch_get_local_results_slow_path(
        self,
        op_call: torch._ops.OpOverload,
        args: tuple[object, ...],
        op_info: OpInfo,
    ) -> object:
        output_sharding = op_info.output_sharding
        if output_sharding is None:
            raise AssertionError("output sharding should not be None")
        if op_info is None:
            raise AssertionError("op_info should never be None")

        # Record output placements for debugging
        debug_mode = get_active_debug_mode()
        if debug_mode is not None and output_sharding.output_spec is not None:
            debug_mode.record_output_placements(output_sharding.output_spec)

        mesh = op_info.compute_mesh
        participating = mesh._is_current_rank_part_of_mesh()
        local_results = None
        if participating:
            # computation that happens in the current rank of the mesh, normal case
            if output_sharding.needs_redistribute:
                # If sharding propagation decision needs redistribute, perform redistribute
                # on args first, which could potentially modify args (i.e. allgather certain arg)
                if output_sharding.redistribute_schema is None:
                    raise AssertionError
                self.redistribute_local_args(
                    op_info,
                    output_sharding.redistribute_schema,
                    output_sharding.use_val_from_redistribute_schema,
                )

            local_tensor_args = (
                pytree.tree_unflatten(
                    cast(list[object], op_info.local_args),
                    # pyrefly: ignore [bad-argument-type]
                    op_info.args_tree_spec,
                )
                if op_info.args_tree_spec
                else op_info.local_args
            )

            # run local op computation with potentially modified args/kwargs
            local_tensor_args = cast(tuple[object, ...], local_tensor_args)
            if op_call in self._random_ops:
                if not random._rng_tracker and is_rng_supported_mesh(mesh):
                    # Default to `OffsetBasedRNGTracker` if the parallelism API did not already construct one
                    # Skip RNG state sync during tracing to avoid lazily initializing real RNG state under fake mode.
                    run_state_sync = not _are_we_tracing()
                    if not run_state_sync:
                        logger.info(
                            "DTensor RNG tracker is being lazily initialized during tracing. "
                            "RNG states may not be synchronized across ranks, which can lead "
                            "to silent incorrectness. Please call `torch.manual_seed()` with "
                            "the same seed on all ranks before compiling DTensor random ops.",
                            stacklevel=2,
                        )
                    random._rng_tracker = random.OffsetBasedRNGTracker(
                        mesh, run_state_sync
                    )

                first_arg, first_local_arg = (
                    cast(dtensor.DTensor, args[0]),
                    cast(torch.Tensor, local_tensor_args[0]),
                )

                # If the user provided a generator, we hook it up to our RNG manager, but we also pop it from kwargs
                # so the op_call does not directly use it (we want op_call to fall back to the 'default' which is
                # our RNG manager)
                maybe_user_generator = op_info.local_kwargs.pop("generator", None)
                if not (
                    maybe_user_generator is None
                    or isinstance(maybe_user_generator, torch.Generator)
                ):
                    raise AssertionError

                if (
                    random._rng_tracker
                    and not first_local_arg.is_meta
                    and random._rng_tracker.distribute_region_enabled
                ):
                    if (
                        maybe_user_generator is not None
                        or first_local_arg.device.type != "cuda"
                        or (
                            not _are_we_tracing()
                            and type(first_local_arg) is not torch.Tensor
                        )
                    ):
                        with random._rng_tracker._distribute_region(
                            first_arg._spec, generator=maybe_user_generator
                        ):
                            local_results = op_call(
                                *local_tensor_args, **op_info.local_kwargs
                            )
                    else:
                        # CUDA device without user generator, use HOP for traceability
                        if not isinstance(
                            random._rng_tracker, random.OffsetBasedRNGTracker
                        ):
                            raise AssertionError
                        start_offset_incr, end_offset_incr = (
                            random._rng_tracker._compute_rng_offsets(first_arg._spec)
                        )
                        local_results = run_dtensor_rng_op(
                            start_offset_incr,
                            end_offset_incr,
                            op_call,
                            *local_tensor_args,
                            **op_info.local_kwargs,
                        )
                else:
                    # No rng_tracker, meta tensor, or distribute_region disabled
                    local_results = op_call(*local_tensor_args, **op_info.local_kwargs)
            else:
                # normal case, run local sharded op computation
                if (
                    output_sharding.needs_redistribute
                    and output_sharding.redistribute_schema is not None
                    and output_sharding.redistribute_schema.op != op_call
                ):
                    # Op was rewritten (e.g., squeeze.default → squeeze.dims)
                    local_results = output_sharding.redistribute_schema.op(
                        *local_tensor_args, **op_info.local_kwargs
                    )
                else:
                    local_results = op_call(*local_tensor_args, **op_info.local_kwargs)

        else:
            # For a non-participating device (happens on rank that does not belong to
            # the device mesh), we do:
            #   1. if the return type is scalar, set the local result to None.
            #   2. if the return type is Tensor or List[Tensor], return empty
            #   tensor(s) with correct dtype.
            spec = output_sharding.output_spec
            ret_list = op_call._schema.returns

            if spec is None:
                # For a scalar return type, the non-participating device has None
                # as its local result
                local_results = None
            else:

                def default_tensor(spec: DTensorSpec) -> torch.Tensor:
                    if spec.tensor_meta is not None:
                        shape = spec.tensor_meta.shape
                        dtype = spec.tensor_meta.dtype
                        if len(shape) == 0:
                            # scalar tensor
                            return torch.zeros((), dtype=dtype)
                        else:
                            # non-scalar tensor
                            return torch.tensor([], dtype=dtype)
                    else:
                        raise RuntimeError(f"{spec} has no tensor metadata.")

                if isinstance(spec, DTensorSpec):
                    # return a Tensor value
                    local_results = default_tensor(spec)
                elif isinstance(spec, Sequence):
                    # return a List[Tensor] value
                    local_results = [
                        default_tensor(s) if s is not None else None for s in spec
                    ]
                    if not isinstance(local_results, list):
                        raise AssertionError
                    if None in local_results:
                        ret_type = str(ret_list[0].type)
                        raise NotImplementedError(
                            f"return type {ret_type} in DTensor op is not supported"
                        )
        return local_results
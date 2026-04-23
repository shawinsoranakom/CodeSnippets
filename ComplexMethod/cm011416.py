def propagate_op_sharding_non_cached(self, op_schema: OpSchema) -> OutputSharding:
        """
        Propagate the sharding for an operator given the op_schema.
        """
        # no-op in OSS, logs API usage metrics in meta-internal runs
        torch._C._log_api_usage_once(
            "torch.distributed.tensor._sharding_prop.ShardingPropagator.propogate_op_sharding_non_cached"
        )
        # special case op, we don't need to propagate for local
        # scalar. TODO: figure out a better way to handle this
        if op_schema.op is aten._local_scalar_dense.default:
            return OutputSharding(None, op_schema)

        out_tensor_meta = self._propagate_tensor_meta_non_cached(op_schema)

        single_dim_strategy_info = self.op_single_dim_strategy_funcs.get(op_schema.op)
        op_strategy_func = self.op_strategy_funcs.get(op_schema.op)
        decomp_exception = None
        if single_dim_strategy_info is not None or op_strategy_func is not None:
            # Validate that tensor_meta count matches expected outputs from op schema.
            # This catches bugs in fake tensor propagation early.
            if single_dim_strategy_info is not None:
                _validate_tensor_meta_count(op_schema, out_tensor_meta)
            """
            Given the single_dim_strategy, which is just a minimal set of valid input-output placement specifications
            for the operator over a single mesh dimension,

            And the OpSchema, which includes information about the runtime input tensor placements, and the mesh,

            Combine single_dim_strategies across mesh dims, also expanding placeholders (ShardPlaceholder) to any real
            sharding types in op_schema, and find the lowest cost redistribution of inputs to match a valid strategy
            combination.
            """
            # wrap the op_schema with op strategy for sharding strategy propagation
            strategy_schema = self._wrap_with_op_strategy(op_schema)

            if single_dim_strategy_info is not None:
                mesh = try_find_mesh_from_args(op_schema.op, op_schema.args_schema)
                if not isinstance(mesh, DeviceMesh):
                    raise AssertionError("Expected to find a valid mesh")
                # expand to generate the full set of strategy combinations, each one
                # with a redistribute cost, and then find the min strategy over those costs.
                _expanded_strategy_fn = _expand_single_dim_strategy_to_mesh(
                    mesh, strategy_schema, single_dim_strategy_info, out_tensor_meta
                )
                op_strategy = _expanded_strategy_fn(
                    op_schema.op, strategy_schema.args_meta, strategy_schema.kwargs_meta
                )
            else:
                if op_strategy_func is None:
                    raise AssertionError
                op_strategy = op_strategy_func(strategy_schema)

        else:
            # try operator decomposition path

            op_strategy = None
            if DecompShardingStrategy.has_decomp(op_schema.op):
                # Ensure schema_info is registered for proper cache key computation
                self.decomp_strategy.ensure_schema_info(op_schema.op)
                try:
                    op_strategy = self.decomp_strategy.propagate_strategy(
                        op_schema,
                    )
                except Exception as e:
                    decomp_exception = e

        if op_strategy is not None:
            if isinstance(op_strategy, OpStrategy):
                _propagate_use_strided_shard_flag(op_strategy, op_schema)
                # single Op strategy
                output_strategy = _select_min_cost_strategy(op_strategy, op_schema)

                # check if we need to redistribute the input
                needs_redistribute = False
                # check if we want to use args value from redistribute_schema
                use_val_from_redistribute_schema = False
                expected_input_specs: list[DTensorSpec] = []

                # in case where the op does not specify input_specs and output_specs
                # is a DTensorSpec, we use output_specs as the spec for each DTensor
                # input arg.
                if output_strategy.input_specs is None:
                    if not isinstance(output_strategy.output_specs, DTensorSpec):
                        raise AssertionError

                for idx, input_spec in enumerate(op_schema.args_spec):
                    desired_spec = (
                        output_strategy.output_spec
                        if output_strategy.input_specs is None
                        else output_strategy.input_specs[idx]
                    )
                    expected_input_specs.append(
                        desired_spec.shallow_copy_with_tensor_meta(
                            input_spec.tensor_meta
                        )
                    )
                    if input_spec.placements != desired_spec.placements:
                        needs_redistribute = True

                suggestion_schema = None
                if needs_redistribute:
                    suggestion_schema = OpSchema(
                        op_schema.op, tuple(expected_input_specs), {}
                    )
                    suggestion_schema._inplace_rewrap_schema_suggestion(op_schema)

                # shape and stride args need to be modified for
                # view ops and new factory ops, potentially
                if op_schema.op in self.op_to_shape_and_stride_idx:
                    if not isinstance(output_strategy.output_spec, DTensorSpec):
                        raise AssertionError
                    # It happens when the output has the same shape as the input
                    # and the input placements are not all Replicate().
                    if any(
                        isinstance(p, Shard | _StridedShard)
                        for p in output_strategy.output_spec.placements
                    ):
                        schema = suggestion_schema or op_schema
                        if not isinstance(out_tensor_meta, TensorMeta):
                            raise AssertionError
                        suggestion_schema = self._adjust_shape_and_stride_args(
                            out_tensor_meta, schema, output_strategy.output_spec
                        )
                        needs_redistribute = True
                        use_val_from_redistribute_schema = True

                # adjust individual scalar shape args (e.g. N, C, HxW in group_norm)
                if op_schema.op in self.op_to_scalar_shape_adjuster:
                    if any(
                        isinstance(p, Shard | _StridedShard)
                        for spec in expected_input_specs
                        for p in spec.placements
                    ):
                        schema = suggestion_schema or op_schema
                        adjuster = self.op_to_scalar_shape_adjuster[op_schema.op]
                        suggestion_schema = adjuster(expected_input_specs, schema)
                        needs_redistribute = True
                        use_val_from_redistribute_schema = True

                # rewrite squeeze to use only globally-singleton dims
                if op_schema.op in self.squeeze_op_to_dims_variant:
                    schema = suggestion_schema or op_schema
                    adjusted = self._adjust_squeeze_to_global_singletons(schema)
                    if adjusted is not None:
                        suggestion_schema = adjusted
                        needs_redistribute = True
                        use_val_from_redistribute_schema = True

                # construct output spec for the op
                if op_schema.return_type_tuple_tensor_like():
                    # for ops that return multiple tensors and the output_specs is not
                    # a tuple, we use a tuple of that single output spec as the new
                    # output_specs
                    output_specs: OutputSpecType = output_strategy.output_specs
                    if isinstance(output_specs, DTensorSpec):
                        output_specs = tuple(
                            # create a new DTensorSpec with the same placement as the
                            # output_specs in output_strategy
                            DTensorSpec(
                                mesh=output_specs.mesh,
                                placements=output_specs.placements,
                                tensor_meta=output_specs.tensor_meta,
                                use_strided_shard_as_shard_order=output_specs.use_strided_shard_as_shard_order,
                            )
                            for _ in range(len(op_schema.op._schema.returns))
                        )
                elif (
                    op_schema.return_type_tensor()
                    or op_schema.return_type_list_tensor_like()
                ):
                    output_specs = output_strategy.output_specs
                else:
                    output_specs = None

                output_sharding = OutputSharding(
                    output_specs,
                    suggestion_schema,
                    needs_redistribute=needs_redistribute,
                    use_val_from_redistribute_schema=use_val_from_redistribute_schema,
                )
            elif isinstance(op_strategy, TupleStrategy):
                # tuple strategy output sharding processing
                # runtime select OpSpec for each TupleStrategy input arg
                selected_strategies: list[OpSpec] = []
                out_spec_list: list[DTensorSpec] = []
                for strategy in op_strategy.children:
                    if not isinstance(strategy, OpStrategy):
                        raise AssertionError
                    _propagate_use_strided_shard_flag(strategy, op_schema)
                    selected_strategy = _select_min_cost_strategy(strategy)
                    selected_strategies.append(selected_strategy)
                    if selected_strategy.output_specs is not None:
                        out_spec_list.append(selected_strategy.output_spec)

                needs_redistribute = False
                suggestion_args: list[object] = []
                tensor_or_list_tensor_arg_idx = 0

                for arg in op_schema.args_schema:
                    if (
                        arg
                        and isinstance(arg, (list, tuple))
                        and isinstance(arg[0], DTensorSpec)
                    ):
                        expected_input_spec_list: list[DTensorSpec] = []
                        for idx, arg_spec in enumerate(arg):
                            expected_input_spec = selected_strategies[idx].input_spec(
                                tensor_or_list_tensor_arg_idx
                            )
                            expected_input_spec = (
                                expected_input_spec.shallow_copy_with_tensor_meta(
                                    arg_spec.tensor_meta
                                )
                            )
                            if arg_spec.placements != expected_input_spec.placements:
                                needs_redistribute = True
                            expected_input_spec_list.append(expected_input_spec)
                        suggestion_args.append(
                            tuple(expected_input_spec_list)
                            if isinstance(arg, tuple)
                            else expected_input_spec_list
                        )
                        tensor_or_list_tensor_arg_idx += 1

                    elif isinstance(arg, DTensorSpec):
                        expected_input_spec = selected_strategies[0].input_spec(
                            tensor_or_list_tensor_arg_idx
                        )
                        expected_input_spec = (
                            expected_input_spec.shallow_copy_with_tensor_meta(
                                arg.tensor_meta
                            )
                        )
                        if arg.placements != expected_input_spec.placements:
                            needs_redistribute = True
                        suggestion_args.append(expected_input_spec)
                        tensor_or_list_tensor_arg_idx += 1
                    else:
                        suggestion_args.append(arg)

                suggestion_schema = None
                if needs_redistribute:
                    suggestion_schema = OpSchema(
                        op_schema.op, tuple(suggestion_args), op_schema.kwargs_schema
                    )

                output_sharding = OutputSharding(
                    tuple(out_spec_list) if out_tensor_meta is not None else None,
                    suggestion_schema,
                    needs_redistribute=needs_redistribute,
                    use_val_from_redistribute_schema=False,
                )
            else:
                raise ValueError("Unsupported op strategy type")

            # associate the output sharding with the output tensor metadata
            new_output_spec = self._create_output_spec_with_new_tensor_meta(
                op_schema.op, output_sharding.output_spec, out_tensor_meta
            )
            output_sharding.output_spec = new_output_spec
            return output_sharding
        elif op_schema.op in self.op_to_rules:
            # propagate the sharding with rule
            sharding_prop_func = self.op_to_rules[op_schema.op]

            # step 1. there's sharding propagation rule, run
            # sharding propagation to get the output sharding
            try:
                output_sharding = sharding_prop_func(op_schema)
            except NotImplementedError as e:
                raise e
            except Exception as e:
                raise RuntimeError(
                    f"Sharding propagation failed on op {op_schema}.\nError: {e}"
                ) from e

            # step 2. if can't get output_spec from sharding
            # propagation (i.e. no rules apply for input
            # placements), we return the output sharding
            # with schema suggestions, which can be used to
            # decide how to do redistribute on inputs
            if output_sharding.output_spec is None:
                if output_sharding.redistribute_schema is None:
                    raise RuntimeError(
                        f"Sharding propagation failed on op {op_schema}!"
                    )
                else:
                    # we do auto redistribute on inputs if necessary
                    # run sharding propagation again with suggested schema
                    propagation_res = sharding_prop_func(
                        output_sharding.redistribute_schema
                    )
                    # we set the output sharding with the new propagation result
                    # so that dispatching know both output_spec and redistribute_schema
                    # exist, which indicates a reshard is needed
                    output_sharding.output_spec = propagation_res.output_spec
                    output_sharding.needs_redistribute = True

            # associate the output sharding with the output tensor metadata
            new_output_spec = self._create_output_spec_with_new_tensor_meta(
                op_schema.op, output_sharding.output_spec, out_tensor_meta
            )
            output_sharding.output_spec = new_output_spec

            return output_sharding
        else:
            raise NotImplementedError(
                f"Operator {op_schema.op} does not have a sharding strategy registered."
            ) from decomp_exception
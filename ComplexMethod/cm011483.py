def __init__(
        self,
        strategy_fn: _SingleDimStrategyInfo
        | Callable[
            [OpOverload, ArgsType, KwargsType],
            list[list[Placement | _ShardingPlaceholder]],
        ],
        op_schema: OpSchema,
        output_tensor_meta: TensorMeta | Sequence[TensorMeta | None] | None,
        num_inputs: int | None = None,
    ) -> None:
        # Note: circular import
        from torch.distributed.tensor.placement_types import Partial

        if isinstance(strategy_fn, _SingleDimStrategyInfo):
            self.allow_unbacked_sharding = strategy_fn.allow_unbacked_sharding
            self.allow_uneven_sharding = strategy_fn.allow_uneven_sharding
            different_mesh_args = strategy_fn.different_mesh_args
            func = strategy_fn.func
        else:
            self.allow_unbacked_sharding = None
            self.allow_uneven_sharding = False
            different_mesh_args = None
            func = strategy_fn

        # Determine element_mesh from the first OpStrategy arg.  For foreach
        # per-element schemas the element's inputs may live on a smaller
        # sub-mesh than the global compute_mesh.
        self.element_mesh: DeviceMesh | None = None
        for arg in op_schema.args_schema:
            if isinstance(arg, OpStrategy):
                self.element_mesh = arg.strategies[0].output_spec.mesh
                break

        # Validate that all inputs are on the same mesh (except
        # different_mesh_args which are explicitly allowed to differ).
        if self.element_mesh is not None:
            allowed = set(different_mesh_args or [])
            for i, arg in enumerate(op_schema.args_schema):
                if isinstance(arg, OpStrategy) and i not in allowed:
                    arg_mesh = arg.strategies[0].output_spec.mesh
                    if arg_mesh != self.element_mesh:
                        raise ValueError(
                            f"Cannot run {op_schema.op} on inputs with different "
                            f"meshes: got {self.element_mesh} and {arg_mesh}"
                        )

        # Remap different_mesh_args from args_schema positions to
        # OpStrategy-only positions.  Non-OpStrategy args (e.g. empty lists)
        # are filtered out by expand_to_full_mesh_op_strategy, shifting later
        # indices.
        self.remapped_different_mesh_args: list[int] | None = None
        if different_mesh_args is not None:
            schema_to_strategy: dict[int, int] = {}
            strategy_pos = 0
            for schema_pos, arg in enumerate(op_schema.args_schema):
                if isinstance(arg, OpStrategy):
                    schema_to_strategy[schema_pos] = strategy_pos
                    strategy_pos += 1
            self.remapped_different_mesh_args = [
                schema_to_strategy[i]
                for i in different_mesh_args
                if i in schema_to_strategy
            ]

        if num_inputs is None:
            num_inputs = _get_num_tensor_inputs(op_schema)
        self.num_inputs = num_inputs

        # Strategy functions may return None in output positions for masked-off
        # outputs (e.g. backward ops with output_mask). Widen the type here.
        strategies_with_placeholders = cast(
            list[list[Placement | _ShardingPlaceholder | None]],
            func(op_schema.op, op_schema.args_meta, op_schema.kwargs_meta),
        )

        # Validate strategy length against the op schema. The schema is the
        # ground truth for num_outputs; combined with num_inputs (which counts
        # all tensor args + kwargs), it gives the expected strategy length.
        # A mismatch means the strategy is missing kwargs placements or has
        # extra entries.
        if len(strategies_with_placeholders) > 0:
            schema_num_outputs = sum(
                1 for r in op_schema.op._schema.returns if "Tensor" in str(r.type)
            )
            expected_len = schema_num_outputs + num_inputs
            actual_len = len(strategies_with_placeholders[0])
            if actual_len != expected_len:
                raise AssertionError(
                    f"Strategy length {actual_len} != expected {expected_len} "
                    f"(schema_outputs={schema_num_outputs} + inputs={num_inputs}) "
                    f"for {op_schema.op}. Strategies must include placements "
                    f"for all outputs, args, and tensor kwargs."
                )

        # Compute num_outputs from strategy structure or output_tensor_meta
        if len(strategies_with_placeholders) > 0:
            num_outputs = len(strategies_with_placeholders[0]) - num_inputs
        elif output_tensor_meta is None:
            num_outputs = 0
        elif isinstance(output_tensor_meta, TensorMeta):
            num_outputs = 1
        else:
            num_outputs = len(output_tensor_meta)
        self.num_outputs = num_outputs

        strategies_with_placeholders = _insert_single_dim_replication_strategy(
            strategies_with_placeholders,
            num_outputs,
            num_inputs,
            output_tensor_meta,
        )

        unique_input_placements = _get_unique_placements(op_schema)
        self.expanded_strategies = _fill_single_dim_strategy_placeholders(
            unique_input_placements, strategies_with_placeholders
        )

        # Build strategy lookup: map input placements -> output placements
        self.strategy_lookup = {}
        for strategy in self.expanded_strategies:
            input_key = tuple(strategy[num_outputs:])
            if input_key not in self.strategy_lookup:
                self.strategy_lookup[input_key] = tuple(strategy[:num_outputs])

        # Precompute allowed placements per input from the expanded rules
        self.allowed_sharding_per_input: dict[int, set[Shard | _StridedShard]] = (
            defaultdict(set)
        )
        self.allowed_partial_per_input: dict[int, set[Placement]] = defaultdict(set)
        for strategy in self.expanded_strategies:
            for input_idx in range(num_inputs):
                p = strategy[num_outputs + input_idx]
                if p is None:
                    continue
                if _is_sharding(p):
                    self.allowed_sharding_per_input[input_idx].add(p)
                elif isinstance(p, Partial):
                    self.allowed_partial_per_input[input_idx].add(p)

        # Resolve output tensor_meta per output index
        if output_tensor_meta is None:
            self.output_metas = (None,) * max(num_outputs, 0)
        elif isinstance(output_tensor_meta, TensorMeta):
            self.output_metas = (output_tensor_meta,)
        else:
            self.output_metas = tuple(output_tensor_meta)
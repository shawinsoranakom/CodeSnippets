def grouped_mm_strategy(op_schema: OpSchema) -> OpStrategy:
    mesh = op_schema.get_mesh_from_args()

    mat1_strategy = op_schema.args_schema[0]
    if not isinstance(mat1_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(mat1_strategy)}")
    mat2_strategy = op_schema.args_schema[1]
    if not isinstance(mat2_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(mat2_strategy)}")
    if len(op_schema.args_schema) > 3:
        bias_strategy = op_schema.args_schema[3]
        if bias_strategy is not None:
            raise AssertionError("grouped_mm doesn't support bias yet")

    single_mesh_dim_strategies = []

    offs_placement = None
    if len(op_schema.args_schema) > 2 and op_schema.args_schema[2] is not None:
        offs_placement = Replicate()  # offs should always be replicated

    all_replicate: PlacementList = [
        Replicate(),
        Replicate(),  # mat1
        Replicate(),  # mat2
        offs_placement,  # offs
        None,  # bias
    ]
    partial_replicate: PlacementList = [
        Partial(),
        Partial(),  # mat1
        Replicate(),  # mat2
        offs_placement,  # offs
        None,  # bias
    ]
    replicate_partial: PlacementList = [
        Partial(),
        Replicate(),  # mat1
        Partial(),  # mat2
        offs_placement,  # offs
        None,  # bias
    ]
    single_mesh_dim_strategies = [all_replicate, partial_replicate, replicate_partial]

    if mat1_strategy.ndim == 2 and mat2_strategy.ndim == 3:
        # rowwise_replicate for 2dx3d not supported
        replicate_colwise_2x3: PlacementList = [
            Shard(1),
            Replicate(),  # mat1
            Shard(2),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        colwise_rowwise_2x3: PlacementList = [
            Partial(),
            Shard(1),  # mat1
            Shard(1),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        single_mesh_dim_strategies.extend([replicate_colwise_2x3, colwise_rowwise_2x3])

    if mat1_strategy.ndim == 3 and mat2_strategy.ndim == 2:
        # replicate_colwise for 3dx2d not supported
        colwise_rowwise_3x2: PlacementList = [
            Partial(),
            Shard(2),  # mat1
            Shard(0),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        rowwise_replicate_3x2: PlacementList = [
            Shard(0),
            Shard(1),  # mat1
            Replicate(),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        single_mesh_dim_strategies.extend([colwise_rowwise_3x2, rowwise_replicate_3x2])

    if mat1_strategy.ndim == 2 and mat2_strategy.ndim == 2:
        # colwise_rowwise for 2dx2d not supported
        replicate_colwise_2x2: PlacementList = [
            Shard(2),
            Replicate(),  # mat1
            Shard(1),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        rowwise_replicate_2x2: PlacementList = [
            Shard(1),
            Shard(0),  # mat1
            Replicate(),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        single_mesh_dim_strategies.extend(
            [replicate_colwise_2x2, rowwise_replicate_2x2]
        )

    if mat1_strategy.ndim == 3 and mat2_strategy.ndim == 3:
        replicate_colwise_3x3: PlacementList = [
            Shard(2),
            Replicate(),  # mat1
            Shard(2),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        rowwise_replicate_3x3: PlacementList = [
            Shard(1),
            Shard(1),  # mat1
            Replicate(),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        colwise_rowwise_3x3: PlacementList = [
            Partial(),
            Shard(2),  # mat1
            Shard(1),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        batch_dim_sharding: PlacementList = [
            Shard(0),
            Shard(0),  # mat1
            Shard(0),  # mat2
            offs_placement,  # offs
            None,  # bias
        ]
        single_mesh_dim_strategies.extend(
            [
                replicate_colwise_3x3,
                rowwise_replicate_3x3,
                colwise_rowwise_3x3,
                batch_dim_sharding,
            ]
        )

    def valid_grouped_mm_strides(
        input_specs: list[DTensorSpec],
        output_specs: DTensorSpec | tuple[DTensorSpec | None, ...],
    ) -> bool:
        # 1. compute the local-tensor shape/strides given this sharding proposal
        # 2. apply the logic from the groped_mm meta function
        # UGH the input DTensorSpecs are missing their tensormetas... so i can get them another way
        def local_meta(spec: OpSpec, placements: tuple[Placement, ...]) -> TensorMeta:
            if not isinstance(spec.output_specs, DTensorSpec):
                raise AssertionError(
                    f"Expected DTensorSpec, got {type(spec.output_specs)}"
                )
            if not isinstance(spec.output_specs.tensor_meta, TensorMeta):
                raise AssertionError(
                    f"Expected TensorMeta, got {type(spec.output_specs.tensor_meta)}"
                )
            meta: TensorMeta = spec.output_specs.tensor_meta
            local_shape, _ = compute_local_shape_and_global_offset(
                meta.shape, mesh, placements, skip_offset=True
            )
            local_stride = compute_local_stride(meta.stride, local_shape)
            return TensorMeta(torch.Size(local_shape), local_stride, meta.dtype)

        # pyrefly: ignore [missing-attribute]
        mat1_meta = local_meta(mat1_strategy.strategies[0], input_specs[0].placements)
        # pyrefly: ignore [missing-attribute]
        mat2_meta = local_meta(mat2_strategy.strategies[0], input_specs[1].placements)

        def check_valid_strides(meta: TensorMeta) -> bool:
            # copied from `_meta_grouped_mm_common` in meta_registrations.py
            end_dim = len(meta.shape) - 1
            alignment = 16 // meta.dtype.itemsize
            if meta.stride[end_dim - 1] == 1 and meta.stride[end_dim] >= max(
                1, meta.shape[end_dim - 1]
            ):
                if meta.stride[end_dim] % alignment != 0:
                    return False
            elif meta.stride[end_dim] == 1 and meta.stride[end_dim - 1] >= max(
                1, meta.shape[end_dim]
            ):
                if meta.stride[end_dim - 1] % alignment != 0:
                    return False
            else:
                return False
            return True

        mat1_valid = check_valid_strides(mat1_meta)
        mat2_valid = check_valid_strides(mat2_meta)
        return mat1_valid and mat2_valid

    return expand_to_full_mesh_op_strategy(
        mesh,
        op_schema,
        single_mesh_dim_strategies,
        input_index=1,
        is_valid_strategy_cb=valid_grouped_mm_strides,
    )
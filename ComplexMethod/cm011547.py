def _scaled_dot_product_cudnn_attention_backward_base_strategies(
    op_schema: OpSchema,
) -> list[PlacementList]:
    """Helper that returns list of base placement strategies (without CP)."""
    if len(op_schema.args_schema) < 15:
        raise AssertionError(
            f"Expected at least 15 args_schema, got {len(op_schema.args_schema)}"
        )
    has_attn_bias = op_schema.args_schema[8] is not None
    has_scale = len(op_schema.args_schema) >= 16 and False

    query_strategy = op_schema.args_schema[1]
    if not isinstance(query_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(query_strategy)}")
    # assuming q/k/v have the same shape

    single_mesh_dim_strategies = []

    # placement list stores placements of [outputs, inputs]
    # cudnn outputs: (Tensor dq, Tensor dk, Tensor dv)
    # cudnn inputs: (
    #   Tensor grad_out,
    #   Tensor query,
    #   Tensor key,
    #   Tensor value,
    #   Tensor out,
    #   Tensor logsumexp,
    #   Tensor philox_seed,
    #   Tensor philox_offset,
    #   Tensor attn_bias,
    #   Tensor cum_seq_q,
    #   Tensor cum_seq_k,
    #   SymInt max_q,
    #   SymInt max_k,
    #   float dropout_p,
    #   bool is_causal,
    #   int? scale,
    # )

    # case 1: we can always accept full replication for both inputs and outputs
    all_replicate_out: PlacementList = [
        Replicate(),  # dq
        Replicate(),  # dk
        Replicate(),  # dv
    ]
    all_replicate_inp: PlacementList = [Replicate()] * 6
    all_replicate_inp += [
        Replicate()
    ] * 2  # philox_seed, philox_offset is casted to Replicate() in DTensor
    all_replicate_inp += [Replicate() if has_attn_bias else None]
    all_replicate_inp += [None] * 6
    if has_scale:
        all_replicate_inp.append(None)

    all_replicate: PlacementList = all_replicate_out + all_replicate_inp
    single_mesh_dim_strategies.append(all_replicate)

    # case 2: we can accept the sharding pattern of tensor parallelism, which
    #   shards on the num of head dim
    qkv_sharding = Shard(1)  # num head dim
    output_sharding = Shard(1)  # num head dim
    logsumexp_sharding = Shard(1)  # num head dim

    num_heads_dim_sharding_out: PlacementList = [qkv_sharding] * 3
    num_heads_dim_sharding_inp: PlacementList = [qkv_sharding] * 4
    num_heads_dim_sharding_inp += [output_sharding]
    num_heads_dim_sharding_inp += [logsumexp_sharding]
    num_heads_dim_sharding_inp += [
        Replicate()
    ] * 2  # philox_seed, philox_offset is casted to Replicate() in DTensor
    num_heads_dim_sharding_inp += [Shard(1) if has_attn_bias else None]
    num_heads_dim_sharding_inp += [None] * 6
    if has_scale:
        num_heads_dim_sharding_inp.append(None)

    num_heads_dim_sharding = num_heads_dim_sharding_out + num_heads_dim_sharding_inp
    single_mesh_dim_strategies.append(num_heads_dim_sharding)

    # case 3: we can accept the sharding pattern of batch parallelism, which
    #   shards on the batch dimension
    qkv_sharding = Shard(0)
    output_sharding = Shard(0)
    logsumexp_sharding = Shard(0)

    batch_dim_sharding_out: PlacementList = [qkv_sharding] * 3
    batch_dim_sharding_inp: PlacementList = [qkv_sharding] * 4
    batch_dim_sharding_inp += [output_sharding]
    batch_dim_sharding_inp += [logsumexp_sharding]
    batch_dim_sharding_inp += [
        Replicate()
    ] * 2  # philox_seed, philox_offset is casted to Replicate() in DTensor
    batch_dim_sharding_inp += [Shard(0) if has_attn_bias else None]
    batch_dim_sharding_inp += [None] * 6
    if has_scale:
        batch_dim_sharding_inp.append(None)

    batch_dim_sharding = batch_dim_sharding_out + batch_dim_sharding_inp
    single_mesh_dim_strategies.append(batch_dim_sharding)

    return single_mesh_dim_strategies
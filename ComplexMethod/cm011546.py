def _scaled_dot_product_cudnn_attention_base_strategies(
    op_schema: OpSchema,
) -> list[PlacementList]:
    """Helper that returns list of base placement strategies (without CP)."""
    (
        query_strategy,  # query
        _,  # key
        _,  # value
        attn_bias_strategy,
        compute_log_sumexp,  # compute_log_sumexp
        *rest_args,  # optional args: dropout_p, is_causal, return_debug_mask, scale
    ) = op_schema.args_schema
    return_debug_mask = len(op_schema.args_schema) >= 8 and rest_args[2]
    has_attn_bias = attn_bias_strategy is not None
    debug_attn_mask_sharding: Placement | None = (
        Replicate() if return_debug_mask else None
    )

    if not isinstance(query_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(query_strategy)}")
    # assuming q/k/v have the same shape

    single_mesh_dim_strategies = []

    # placement list stores placements of [outputs, inputs]
    # in the spda case, we have 2 valid tensor outputs and 3 tensor inputs
    # first we can always accept full replication for both inputs and outputs
    all_replicate: PlacementList = [
        Replicate(),  # output
        Replicate(),  # logsumexp
        None,  # cum_seq_q
        None,  # cum_seq_k
        None,  # max_q
        None,  # max_k
        None,  # philox_seed
        None,  # philox_offset
        # NOTE: debug_attn_mask is not supported by pytorch and is always an empty tensor
        # https://github.com/pytorch/pytorch/blob/60205b0eb2602317856312a66d955c88334ade0b/aten/src/ATen/native/transformers/cuda/attention.cu#L839-L840
        debug_attn_mask_sharding,  # debug_attn_mask
        Replicate(),  # q
        Replicate(),  # k
        Replicate(),  # v
    ]
    if has_attn_bias:
        all_replicate.append(Replicate())  # attn bias

    single_mesh_dim_strategies.append(all_replicate)

    # second we can accept the sharding pattern of tensor parallelism, which
    # shard on the num of head dim
    tp_sharding = Shard(1)  # num head dim
    qkv_sharding = tp_sharding
    output_sharding = tp_sharding
    logsumexp_sharding = tp_sharding if compute_log_sumexp else Replicate()
    debug_attn_mask_sharding = tp_sharding if return_debug_mask else None

    num_heads_dim_sharding: PlacementList = [
        output_sharding,
        logsumexp_sharding,
        None,  # cum_seq_q
        None,  # cum_seq_k
        None,  # max_q
        None,  # max_k
        None,  # philox_seed
        None,  # philox_offset
        debug_attn_mask_sharding,
        qkv_sharding,
        qkv_sharding,
        qkv_sharding,
    ]
    single_mesh_dim_strategies.append(num_heads_dim_sharding)

    # batch parallelism
    logsumexp_sharding = Shard(0) if compute_log_sumexp else Replicate()
    debug_attn_mask_sharding = Shard(0) if return_debug_mask else None
    batch_dim_sharding: PlacementList = [
        Shard(0),  # output
        logsumexp_sharding,
        None,  # cum_seq_q
        None,  # cum_seq_k
        None,  # max_q
        None,  # max_k
        None,  # philox_seed
        None,  # philox_offset
        debug_attn_mask_sharding,
        Shard(0),  # q
        Shard(0),  # k
        Shard(0),  # v
    ]
    single_mesh_dim_strategies.append(batch_dim_sharding)

    return single_mesh_dim_strategies
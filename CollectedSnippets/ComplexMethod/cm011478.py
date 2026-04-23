def _insert_single_dim_replication_strategy(
    single_dim_strategies_with_placeholders: list[
        list[Placement | _ShardingPlaceholder | None]
    ],
    num_outputs: int,
    num_input_tensors: int,
    output_tensor_meta: TensorMeta | Sequence[TensorMeta | None] | None = None,
) -> list[list[Placement | _ShardingPlaceholder | None]]:
    """
    Inserts the [Replicate(), Replicate(), ...] strategy after asserting that such strategy does not yet exist.
    For ops with masked-off outputs (e.g. backward ops with output_mask), output positions
    where output_tensor_meta is None are set to None in the all-Replicate rule.
    """
    for strategy in single_dim_strategies_with_placeholders:
        if all(isinstance(p, Replicate) or p is None for p in strategy):
            return single_dim_strategies_with_placeholders
    total_len = num_outputs + num_input_tensors
    replicate_rule: list[Placement | _ShardingPlaceholder | None] = [
        Replicate()
    ] * total_len
    # Set None for masked-off output positions based on output_tensor_meta
    if isinstance(output_tensor_meta, Sequence):
        for i, meta in enumerate(output_tensor_meta):
            if meta is None and i < num_outputs:
                replicate_rule[i] = None
    single_dim_strategies_with_placeholders.insert(0, replicate_rule)
    return single_dim_strategies_with_placeholders
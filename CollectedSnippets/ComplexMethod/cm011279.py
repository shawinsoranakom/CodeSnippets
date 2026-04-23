def _shard_dict_of_args(
    args_dict,
    args_chunk_spec,
    num_chunks,
):
    """
    Given a dictionary of args, and a dictionary of chunking specs, shard the
    args according to the chunking specs.

    Args:
        args_dict: Dictionary of args
        args_chunk_spec: Dictionary of chunking specs
        num_chunks: Number of chunks to shard the args into

    Returns:
        args_split: List of sharded args
    """

    if not args_dict:
        return [{} for _ in range(num_chunks)]

    if not len(args_dict) == len(args_chunk_spec):
        raise AssertionError(
            f"args_dict.keys() = {list(args_dict.keys())} "
            f"args_chunk_spec.keys() = {list(args_chunk_spec.keys())}"
        )
    if args_chunk_spec is None:
        raise AssertionError("args_chunk_spec should have been set by caller")

    values, tree_spec = tree_flatten(
        args_dict, is_leaf=lambda x: isinstance(x, BlockMask)
    )
    chunk_specs, _ = tree_flatten(
        args_chunk_spec, is_leaf=lambda x: isinstance(x, BlockMask)
    )

    # First check and find the actual number of chunks
    split_sizes = []
    for v, spec in zip(values, chunk_specs, strict=True):
        # The original logic is "spec is _Replicate". This doesn't seem to be
        # correct. But we keep it for backward compatibility.
        if spec is _Replicate or isinstance(spec, _Replicate):
            split_sizes.append(num_chunks)
        elif isinstance(v, torch.Tensor):
            if not isinstance(spec, TensorChunkSpec):
                raise AssertionError(f"Expected TensorChunkSpec, got {type(spec)}")
            split_sizes.append(v.size(spec.split_dim))
        elif isinstance(v, BlockMask):
            if not isinstance(spec, TensorChunkSpec):
                raise AssertionError(f"Expected TensorChunkSpec, got {type(spec)}")
            if not spec.split_dim == 0:
                raise AssertionError("BlockMask only supports split_dim=0")
            # BlockMask will broadcast if B is 1.
            if v.kv_num_blocks.size(0) == 1:
                split_sizes.append(num_chunks)
            else:
                split_sizes.append(v.kv_num_blocks.size(0))
        else:
            raise ValueError(
                f"Unsupported chunk spec: {spec} and value: {v} combination."
            )
    result_num_chunks = min(*split_sizes, num_chunks)

    flat_split_results: list[Any] = [[] for _ in range(result_num_chunks)]
    for v, spec in zip(values, chunk_specs, strict=True):
        v_splits: Sequence[Any] = []
        if spec is _Replicate or isinstance(spec, _Replicate):
            v_splits = [v] * result_num_chunks
        elif isinstance(v, torch.Tensor):
            v_splits = _split_tensor(v, spec, result_num_chunks)
        elif isinstance(v, BlockMask):
            v_splits = _split_block_mask(v, result_num_chunks)
        else:
            raise ValueError(
                f"Unsupported chunk spec: {spec} and value: {v} combination."
            )

        for _flat_split_result, _v_split in zip(
            flat_split_results, v_splits, strict=True
        ):
            _flat_split_result.append(_v_split)

    return [
        tree_unflatten(_flat_split_result, tree_spec)
        for _flat_split_result in flat_split_results
    ]
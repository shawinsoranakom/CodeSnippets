def validate_fp8_block_shape(
    layer: torch.nn.Module,
    input_size: int,
    output_size: int,
    input_size_per_partition: int,
    output_partition_sizes: list[int],
    block_size: list[int],
) -> None:
    """Validate block quantization shapes for tensor parallelism."""
    from vllm.distributed import get_tensor_model_parallel_world_size

    if getattr(layer, "allow_fp8_block_shape_mismatch", False):
        logger.debug(
            "Skipping FP8 block shape validation for layer %s due to detected"
            " mismatch allowance.",
            getattr(layer, "prefix", "<unknown>"),
        )
        return

    tp_size = getattr(layer, "tp_size", get_tensor_model_parallel_world_size())
    block_n, block_k = block_size[0], block_size[1]

    # Required by row parallel
    if (
        tp_size > 1
        and input_size // input_size_per_partition == tp_size
        and input_size_per_partition % block_k != 0
    ):
        raise ValueError(
            f"Weight input_size_per_partition = {input_size_per_partition} "
            f"is not divisible by weight quantization block_k = {block_k}."
        )

    # Required by column parallel or enabling merged weights
    is_tp_split = tp_size > 1 and output_size // sum(output_partition_sizes) == tp_size
    is_merged_gemm = len(output_partition_sizes) > 1
    if is_tp_split or is_merged_gemm:
        sizes_to_check = output_partition_sizes
        if not is_tp_split and is_merged_gemm:
            # In case of merged matrices, we allow the last
            # matrix to not be a multiple of block size
            sizes_to_check = output_partition_sizes[:-1]
        for output_partition_size in sizes_to_check:
            if output_partition_size % block_n != 0:
                raise ValueError(
                    f"Weight output_partition_size = "
                    f"{output_partition_size} is not divisible by "
                    f"weight quantization block_n = {block_n}."
                )
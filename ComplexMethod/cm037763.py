def get_default_config(
    M: int,
    E: int,
    N: int,
    K: int,
    topk: int,
    dtype: str | None,
    block_shape: list[int] | None = None,
) -> dict[str, int]:
    if envs.VLLM_BATCH_INVARIANT:
        return {
            "BLOCK_SIZE_M": 64,
            "BLOCK_SIZE_N": 64,
            "BLOCK_SIZE_K": 32,
            "GROUP_SIZE_M": 8,
            "SPLIT_K": 1,
        }

    # num_stages can cause triton.runtime.errors.OutOfResources on ROCm.
    num_stages_rocm = 2

    if dtype == "fp8_w8a8" and block_shape is not None:
        # Block-wise quant: tile sizes are constrained by block_shape.
        # Use a small M tile for decode-like batches where tokens are
        # spread thin across experts. Larger batches benefit from
        # GROUP_SIZE_M > 1 because the per-block scales add memory
        # traffic that benefits from L2 tile reuse.
        config = {
            "BLOCK_SIZE_M": 16 if M <= 64 else 64,
            "BLOCK_SIZE_N": block_shape[0],
            "BLOCK_SIZE_K": block_shape[1],
            "GROUP_SIZE_M": 1 if M <= 16 else 32,
            "SPLIT_K": 1,
            "num_warps": 4,
            "num_stages": 3 if not current_platform.is_rocm() else num_stages_rocm,
        }
    elif dtype in ["int4_w4a16", "int8_w8a16"] and block_shape is not None:
        # moe wna16 kernels
        # only set BLOCK_SIZE_M
        # BLOCK_SIZE_N and BLOCK_SIZE_K would be set later
        bit = 4 if dtype == "int4_w4a16" else 8
        use_moe_wna16_cuda = should_moe_wna16_use_cuda(M * topk, block_shape[1], E, bit)
        if use_moe_wna16_cuda:
            config = {"BLOCK_SIZE_M": min(16, M), "SPLIT_K": 1}
        elif M <= 20:
            config = {"BLOCK_SIZE_M": 16, "GROUP_SIZE_M": 1, "SPLIT_K": 1}
        elif M <= 40:
            config = {"BLOCK_SIZE_M": 32, "GROUP_SIZE_M": 1, "SPLIT_K": 1}
        else:
            config = {"BLOCK_SIZE_M": 64, "GROUP_SIZE_M": 1, "SPLIT_K": 1}
    else:
        # General defaults for bf16/fp16 and fp8 per-tensor.
        # Tile sizes scale with batch: small batches are memory-bound
        # (favor tall-K tiles), large batches are compute-bound (favor
        # large M/N tiles with more warps).
        if M <= 32:
            block_m = 16
        elif M <= 96:
            block_m = 32
        elif M <= 512:
            block_m = 64
        else:
            block_m = 128

        block_n = 64 if M <= 64 else 128

        # Small batches benefit from longer reduction (larger K tile),
        # while large batches prefer more output parallelism.
        # FP8 elements are half-width so larger K tiles are always cheap.
        block_k = 128 if dtype == "fp8_w8a8" or M <= 64 else 64

        # Grouping adjacent M-blocks lets them share weight tiles in L2.
        # Only helps when there are enough M-blocks per expert to group;
        # with many experts each one sees few tokens so grouping is useless.
        tokens_per_expert = M // max(E, 1)
        group_m = 16 if tokens_per_expert > 128 else 1

        # Large batches have enough blocks to saturate the GPU, so we
        # use more warps per block to increase arithmetic intensity.
        num_warps = 4 if M <= 128 else 8

        if current_platform.is_rocm():
            num_stages = num_stages_rocm
        elif M <= 32:
            num_stages = 4
        else:
            num_stages = 3

        config = {
            "BLOCK_SIZE_M": block_m,
            "BLOCK_SIZE_N": block_n,
            "BLOCK_SIZE_K": block_k,
            "GROUP_SIZE_M": group_m,
            "SPLIT_K": 1,
            "num_warps": num_warps,
            "num_stages": num_stages,
        }
    return config
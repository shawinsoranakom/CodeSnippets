def get_moe_wna16_block_config(
    config: dict[str, int],
    use_moe_wna16_cuda: bool,
    num_valid_tokens: int,
    size_k: int,
    size_n: int,
    num_experts: int,
    group_size: int,
    real_top_k: int,
    block_size_m: int,
):
    if "BLOCK_SIZE_N" in config and "BLOCK_SIZE_K" in config:
        # optimal block config is set
        return {}
    if not use_moe_wna16_cuda:
        # triton moe wna16 kernel
        if num_valid_tokens // real_top_k == 1:
            # if bs=1, use a smaller BLOCK_SIZE_N
            return {"BLOCK_SIZE_N": 32, "BLOCK_SIZE_K": 64}
        else:
            return {"BLOCK_SIZE_N": 64, "BLOCK_SIZE_K": 32}
    else:
        # cuda moe wna16 kernel
        # set default block_size 128, and increase them when num_blocks
        # is too large.
        block_size_n = 128
        block_size_k = 128
        if block_size_k <= group_size:
            block_size_k = group_size

        num_n_blocks = size_k // block_size_k
        num_k_blocks = size_n // block_size_k
        num_m_blocks = (
            num_valid_tokens + block_size_m - 1
        ) / block_size_m + num_experts
        if num_valid_tokens // real_top_k <= block_size_m:
            num_m_blocks = min(num_m_blocks, num_valid_tokens)
        num_blocks = num_m_blocks * num_n_blocks * num_k_blocks

        if size_k % 256 == 0 and num_blocks >= 256 and block_size_k < 256:
            block_size_k = 256
            num_blocks = num_blocks // (256 // block_size_k)

        if (
            num_m_blocks <= 16
            and size_k % (block_size_k * 2) == 0
            and size_k % (block_size_k * 2) == 0
            and block_size_k <= 512
            and num_blocks >= 512
        ):
            block_size_k = block_size_k * 2
            num_blocks = num_blocks // 2

        if num_blocks > 1024:
            block_size_n = 256
            num_n_blocks = num_n_blocks // 2
            num_blocks = num_blocks // 2

        if size_n <= 1024 and num_blocks >= 1024:
            # The kernel performance got much better with BLOCK_SIZE_N=1024
            # when num_blocks is large, event when N is small.
            # Not sure why, maybe it force the CUDA SM process only one block
            # at the same time.
            block_size_n = 1024

        # Ensure BLOCK_SIZE_K is a divisor of size_k for CUDA kernel compatibility
        block_size_k = _ensure_block_size_k_divisible(size_k, block_size_k, group_size)

        return {"BLOCK_SIZE_N": block_size_n, "BLOCK_SIZE_K": block_size_k}
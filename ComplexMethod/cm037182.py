def get_kernel_options(
    query, block_m, block_n, use_direct_build: bool
) -> dict[str, int | bool]:
    kernel_options: dict[str, int | bool] = {
        "FORCE_USE_FLEX_ATTENTION": True,
    }

    def ensure_divisible(candidate: int, block_size: int) -> int:
        """Pick a kernel block size that divides the logical block."""
        if block_size <= 0:
            return candidate
        candidate = min(candidate, block_size)
        if candidate <= 0:
            return block_size
        if block_size % candidate == 0:
            return candidate

        candidate = math.gcd(candidate, block_size)
        if candidate <= 1:
            return block_size
        return candidate

    if envs.VLLM_BATCH_INVARIANT:
        kernel_options["BLOCK_M"] = 16
        kernel_options["BLOCK_N"] = 16
        kernel_options["IS_DIVISIBLE"] = False
        return kernel_options
    if use_direct_build:
        kernel_options["BLOCK_M"] = block_m
        kernel_options["BLOCK_N"] = block_n
        return kernel_options
    else:
        preferred_block = 32 if query.dtype == torch.float32 else 64
        block_lower_bound = 16

        block_m_candidate = ensure_divisible(preferred_block, block_m)
        block_n_candidate = ensure_divisible(preferred_block, block_n)

        if torch.cuda.is_available():
            device_props = torch.cuda.get_device_properties()
            # ROCm doesn't expose shared_memory_per_block_optin attribute
            # AMD GPUs typically have 64KB LDS (Local Data Share) per workgroup
            if hasattr(device_props, "shared_memory_per_block_optin"):
                max_shared_memory = device_props.shared_memory_per_block_optin
            elif current_platform.is_rocm():
                # ROCm fallback: use 64KB
                max_shared_memory = 65536
            else:
                raise RuntimeError(
                    "Unable to determine shared memory size on this hardware."
                )

            if max_shared_memory < 144 * 1024:
                block_m_candidate = ensure_divisible(
                    max(1, block_m_candidate // 2), block_m
                )
                block_n_candidate = ensure_divisible(
                    max(1, block_n_candidate // 2), block_n
                )

        block_m_candidate = max(block_m_candidate, block_lower_bound)
        block_n_candidate = max(block_n_candidate, block_lower_bound)

        kernel_options["BLOCK_M"] = block_m_candidate
        kernel_options["BLOCK_N"] = block_n_candidate

    return kernel_options
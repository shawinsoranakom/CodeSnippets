def _generate_optimal_warmup_m_values(
    max_tokens: int, n: int, device: torch.device
) -> list[int]:
    """
    Generate M values that cover all possible DeepGEMM kernel configurations.
    Reference: https://github.com/deepseek-ai/DeepGEMM/blob/79f48ee15a82dd5fad5cd9beaa393c1f755e6b55/csrc/jit_kernels/heuristics/common.hpp

    Args:
        max_tokens: Maximum number of tokens to warmup for
        n: The actual N dimension from the weight tensor
        device: The torch device to get properties from.
    """

    # DeepGEMM's possible block sizes
    block_ms = [64, 128, 256]
    block_ns = list(range(16, min(257, n + 1), 16))
    num_sms = num_compute_units(device.index)

    m_values = set()

    # Always include small cases
    m_values.update([1, 2, 4] + [i for i in range(8, 65, 8)])

    # Collect M values where different wave patterns occur
    for block_m in block_ms:
        for block_n in block_ns:
            if block_n > n:
                continue

            # Add key M boundaries for this block combination
            for wave in range(1, 11):  # Up to 10 waves
                # M where this block config transitions to next wave
                target_blocks = wave * num_sms
                m = target_blocks * block_m // cdiv(n, block_n)
                if 1 <= m <= max_tokens:
                    m_values.add(m)

            # Add block_m boundaries
            for multiple in range(1, max_tokens // block_m + 1):
                m = multiple * block_m
                if m <= max_tokens:
                    m_values.add(m)

    return sorted(m_values)
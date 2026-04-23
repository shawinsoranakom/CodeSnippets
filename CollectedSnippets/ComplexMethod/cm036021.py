def _get_autotune_configs(inner_loop: str) -> list:
    """
    #### Configs for auto-tuning
    """

    configs = []

    # Possible options for `BLOCK_Q`
    for bq in [64, 128, 256]:
        # Possible options for `BLOCK_K`
        for bk in [64, 128, 256]:
            # If the inner loop is along keys the `BLOCK_Q` must be a multiple of `BLOCK_K` for causal masking
            if inner_loop == 'key' and bq % bk != 0:
                continue
            # Similarly when the inner loop is along queries
            if inner_loop == 'query' and bk % bq != 0:
                continue

            # Number of stages and warps
            for s in [2, 3, 4]:
                for w in [4, 8]:
                    if bq * bk < 128 * 128 and w == 8:
                        continue

                    configs.append(triton.Config({'BLOCK_Q': bq, 'BLOCK_K': bk}, num_stages=s, num_warps=w))

    # **Use `return configs` to autotune. Trying all combinations is slow for testing.**
    return configs[:1]
def match_target_block_product(
    size_hints,
    tiling_scores,
    target_block_product,
    min_block_size=1,
    min_red_block: int | None = 4,
):
    """
    Distribute block sizes across dimensions according to tiling scores,
    aiming to match a target product of block sizes.
    """
    min_red_block = (
        min_block_size if min_red_block is None else max(min_red_block, min_block_size)
    )
    total_score = sum(tiling_scores.values())
    if total_score == 0:
        # just assume even score with no minimum block size
        min_block_size = 1
        tiling_scores = dict.fromkeys(tiling_scores.keys(), target_block_product)
        total_score = target_block_product * len(tiling_scores)

    # First, give each coalescing dimension at least min_block_size
    block_sizes = {}
    relative_scores = {}
    curr_block_product = 1

    for dim, score in tiling_scores.items():
        if score == 0 and "r" not in dim:
            block_sizes[dim] = 1
            relative_scores[dim] = 0
            continue

        size = min_block_size if "r" not in dim else min_red_block
        block_sizes[dim] = size
        curr_block_product *= size
        relative_scores[dim] = score / total_score

    # Scale up dimensions by their relative scores until we reach the target
    while curr_block_product < target_block_product and relative_scores:
        dim, score = max(relative_scores.items(), key=lambda item: item[1])

        # Check if we've hit the max for this dimension
        if (
            block_sizes[dim] >= TRITON_MAX_BLOCK[dim.capitalize()]
            or block_sizes[dim] >= size_hints[dim]
        ):
            del relative_scores[dim]
            continue

        block_sizes[dim] *= 2
        relative_scores[dim] /= 2
        curr_block_product *= 2

    return block_sizes
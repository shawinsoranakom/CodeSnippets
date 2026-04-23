def get_ep_ranks_with_experts_batch(
    expert_ids: np.ndarray,
    num_local_experts: int,
    old_indices: np.ndarray,
    new_indices: np.ndarray,
) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    """
    Get the ranks of the experts that need to be exchanged.

    Args:
        expert_ids: 1D array of expert indices to query.
        num_local_experts: The number of local experts.
        old_indices: The old indices of the experts.
        new_indices: The new indices of the experts.

    Returns:
        A tuple of two dictionaries mapping expert_id to:
        - ranks_to_send: The ranks that have this expert and need to send.
        - ranks_to_recv: The ranks that need to receive this expert.
    """
    ranks_to_send_map: dict[int, list[int]] = {}
    ranks_to_recv_map: dict[int, list[int]] = {}

    # Fast path: if no experts, return empty dicts
    if expert_ids.size == 0:
        return ranks_to_send_map, ranks_to_recv_map

    unique_experts = np.unique(expert_ids)
    num_positions = len(old_indices)
    position_indices = np.arange(num_positions, dtype=np.int32)

    # Vectorized approach: find all positions matching any query expert in one pass
    # Use np.isin to get boolean masks for all relevant positions at once
    old_relevant_mask = np.isin(old_indices, unique_experts)
    new_relevant_mask = np.isin(new_indices, unique_experts)

    # Process old_indices (send ranks)
    if np.any(old_relevant_mask):
        old_relevant_positions = position_indices[old_relevant_mask]
        old_relevant_experts = old_indices[old_relevant_mask]
        old_relevant_ranks = old_relevant_positions // num_local_experts

        # Sort by expert first, then by position (to maintain first-appearance order)
        sort_order = np.lexsort((old_relevant_positions, old_relevant_experts))
        sorted_experts = old_relevant_experts[sort_order]
        sorted_ranks = old_relevant_ranks[sort_order]

        # Find boundaries where expert changes
        expert_boundaries = np.concatenate(
            [[0], np.where(np.diff(sorted_experts) != 0)[0] + 1, [len(sorted_experts)]]
        )

        # For each expert, extract unique ranks in order of first appearance
        for i in range(len(expert_boundaries) - 1):
            start, end = expert_boundaries[i], expert_boundaries[i + 1]
            expert = int(sorted_experts[start])
            expert_ranks = sorted_ranks[start:end]

            # Get unique ranks preserving order
            _, unique_idx = np.unique(expert_ranks, return_index=True)
            unique_ranks = expert_ranks[np.sort(unique_idx)]
            ranks_to_send_map[expert] = unique_ranks.tolist()

    # Process new_indices (recv ranks)
    if np.any(new_relevant_mask):
        new_relevant_positions = position_indices[new_relevant_mask]
        new_relevant_experts = new_indices[new_relevant_mask]
        new_relevant_ranks = new_relevant_positions // num_local_experts

        # Sort by expert first, then by position
        sort_order = np.lexsort((new_relevant_positions, new_relevant_experts))
        sorted_experts = new_relevant_experts[sort_order]
        sorted_ranks = new_relevant_ranks[sort_order]

        # Find boundaries where expert changes
        expert_boundaries = np.concatenate(
            [[0], np.where(np.diff(sorted_experts) != 0)[0] + 1, [len(sorted_experts)]]
        )

        # For each expert, extract unique ranks and exclude local copies
        for i in range(len(expert_boundaries) - 1):
            start, end = expert_boundaries[i], expert_boundaries[i + 1]
            expert = int(sorted_experts[start])
            expert_ranks = sorted_ranks[start:end]

            # Get unique ranks preserving order
            _, unique_idx = np.unique(expert_ranks, return_index=True)
            unique_ranks = expert_ranks[np.sort(unique_idx)]

            # Remove ranks that have local copies (in send map)
            send_ranks_set = set(ranks_to_send_map.get(expert, []))
            recv_ranks_actual = [
                int(r) for r in unique_ranks if r not in send_ranks_set
            ]
            ranks_to_recv_map[expert] = recv_ranks_actual

    # Handle experts that only appear in old (send only) or new (recv only)
    for expert in unique_experts:
        expert = int(expert)
        if expert not in ranks_to_send_map:
            ranks_to_send_map[expert] = []
        if expert not in ranks_to_recv_map:
            ranks_to_recv_map[expert] = []

    return ranks_to_send_map, ranks_to_recv_map
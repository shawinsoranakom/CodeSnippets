def verify_round_robin_pattern(expert_map, ep_rank, ep_size, global_num_experts):
    """Verify that the expert map follows the round_robin pattern."""
    # Calculate expected local experts (supporting non-divisible cases)
    base_experts = global_num_experts // ep_size
    remainder = global_num_experts % ep_size

    local_num_experts = base_experts + 1 if ep_rank < remainder else base_experts

    # Expected expert IDs for this rank in round_robin pattern
    # For non-divisible cases, ranks with extra experts start earlier
    expected_expert_ids = []
    for expert_idx in range(local_num_experts):
        global_expert_id = ep_rank + expert_idx * ep_size
        expected_expert_ids.append(global_expert_id)

    # Check that only expected experts are mapped to this rank
    for global_expert_id in range(global_num_experts):
        if global_expert_id in expected_expert_ids:
            local_expert_id = expert_map[global_expert_id]
            expected_local_id = expected_expert_ids.index(global_expert_id)
            assert local_expert_id == expected_local_id, (
                f"Global expert {global_expert_id} should map to local expert "
                f"{expected_local_id}, got {local_expert_id}"
            )
        else:
            assert expert_map[global_expert_id] == -1, (
                f"Global expert {global_expert_id} should not be mapped to this rank"
            )

    # Verify that all local expert IDs are consecutive starting from 0
    local_expert_ids = [expert_map[global_id] for global_id in expected_expert_ids]
    expected_local_ids = list(range(local_num_experts))
    assert local_expert_ids == expected_local_ids, (
        f"Expected local expert IDs {expected_local_ids}, got {local_expert_ids}"
    )
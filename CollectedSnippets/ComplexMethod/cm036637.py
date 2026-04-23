def verify_redundant_experts_have_same_weights(
    expert_weights: list[list[torch.Tensor]],
    indices: torch.Tensor,
    hidden_sizes: list[int],
    ep_rank: int,
    world_size: int,
    num_local_experts: int,
) -> bool:
    """
    Verify that all replicas of the same logical expert have the same weights.
    """
    num_layers = len(expert_weights)
    total_physical_experts = world_size * num_local_experts

    ok = True
    for layer in range(num_layers):
        # Collect weights for all physical experts for each weight matrix
        all_weights: list[torch.Tensor] = []

        for weight_idx, hidden_size in enumerate(hidden_sizes):
            # Create tensor to store all expert weights
            # Shape: [total_physical_experts, hidden_size]
            gathered_weights = torch.zeros(
                total_physical_experts,
                hidden_size,
                device=expert_weights[layer][weight_idx].device,
                dtype=expert_weights[layer][weight_idx].dtype,
            )

            # Use all_gather to collect expert weights from current node
            # expert_weights[layer][weight_idx] shape:
            # [num_local_experts, hidden_size]
            local_weights = expert_weights[layer][
                weight_idx
            ]  # [num_local_experts, hidden_size]

            # Split tensor along dim 0 into a list for all_gather
            gathered_weights_list = torch.chunk(gathered_weights, world_size, dim=0)

            torch.distributed.all_gather(
                # Output list: each element corresponds to one rank's weights
                list(gathered_weights_list),
                local_weights,  # Input: current rank's local weights
            )

            all_weights.append(gathered_weights)

        # Verify that all replicas of the same logical expert have the same
        # weights
        logical_expert_weights: dict[int, dict[int, torch.Tensor]] = {}

        for physical_pos in range(total_physical_experts):
            logical_expert_id = int(indices[layer, physical_pos].item())

            if logical_expert_id not in logical_expert_weights:
                # First time encountering this logical expert, save its weights
                logical_expert_weights[logical_expert_id] = {
                    weight_idx: all_weights[weight_idx][physical_pos]
                    for weight_idx in range(len(hidden_sizes))
                }
            else:
                # Verify that current physical expert's weights match the
                # previously saved logical expert weights
                for weight_idx in range(len(hidden_sizes)):
                    if not torch.equal(
                        all_weights[weight_idx][physical_pos],
                        logical_expert_weights[logical_expert_id][weight_idx],
                    ):
                        ok = False
                        actual_head = (
                            all_weights[weight_idx][physical_pos][:8]
                            .detach()
                            .cpu()
                            .tolist()
                        )
                        reference_head = (
                            logical_expert_weights[logical_expert_id][weight_idx][:8]
                            .detach()
                            .cpu()
                            .tolist()
                        )
                        print(
                            "verify_redundant_experts_have_same_weights failed: "
                            f"rank={ep_rank}, "
                            f"layer={layer}, weight_idx={weight_idx}, "
                            f"logical_expert={logical_expert_id}, "
                            f"physical_pos={physical_pos}, "
                            f"actual_head={actual_head}, "
                            f"reference_head={reference_head}",
                            flush=True,
                        )

    return ok
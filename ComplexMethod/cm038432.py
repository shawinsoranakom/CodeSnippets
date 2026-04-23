def rearrange_expert_weights_inplace(
    old_global_expert_indices: torch.Tensor,
    new_global_expert_indices: torch.Tensor,
    expert_weights: Sequence[Sequence[torch.Tensor]],
    ep_group: ProcessGroup,
    communicator: EplbCommunicator,
    is_profile: bool = False,
    rank_mapping: dict[int, int] | None = None,
) -> None:
    """
    Rearranges the expert weights in place according to the new expert indices.

    The value of the indices arguments are logical indices of the experts,
    while keys are physical.

    Args:
        old_global_expert_indices: Shape (num_moe_layers, num_physical_experts).
        new_global_expert_indices: Shape (num_moe_layers, num_physical_experts).
        expert_weights: A sequence of shape (num_moe_layers)(weight_count)
            of tensors of shape (num_local_physical_experts, hidden_size_i).
            For example, a linear layer may have up and down projection,
            so weight_count = 2. Each weight's hidden size can be different.
        ep_group: The device process group for expert parallelism.
        communicator: EplbCommunicator instance for P2P communication.
        is_profile (bool): If `True`, do not perform any actual weight copy.
            This is used during profile run, where we only perform dummy
            communications to reserve enough memory for the buffers.
        rank_mapping: A dictionary mapping old rank to new rank.
    """
    if rank_mapping is not None:
        if len(rank_mapping) == ep_group.size():
            # scale down
            new_global_expert_indices = _map_new_expert_indices_with_rank_mapping(
                new_global_expert_indices,
                rank_mapping,
            )
        else:
            # scale up
            old_global_expert_indices = _map_old_expert_indices_with_rank_mapping(
                old_global_expert_indices,
                rank_mapping,
                ep_group.size(),
            )

    assert old_global_expert_indices.shape[1] == new_global_expert_indices.shape[1]

    num_moe_layers, num_physical_experts = old_global_expert_indices.shape
    assert len(expert_weights) == num_moe_layers
    assert len(expert_weights[0]) >= 1

    num_local_physical_experts = expert_weights[0][0].shape[0]
    assert new_global_expert_indices.shape == (num_moe_layers, num_physical_experts)

    ep_size = ep_group.size()
    ep_rank = ep_group.rank()
    assert num_physical_experts == ep_size * num_local_physical_experts

    first_layer_weights = list(expert_weights[0])

    if is_profile:
        if communicator.needs_profile_buffer_reservation:
            # Reserve NCCL communication buffers via a dummy all_gather.
            # Backends that pre-allocate their own transfer buffers
            # skip this to avoid the extra memory spike during profiling.
            weights_buffer: list[torch.Tensor] = [
                torch.empty_like(w) for w in first_layer_weights
            ]
            for weight, buffer in zip(expert_weights[0], weights_buffer):
                dummy_recv_buffer = [buffer for _ in range(ep_size)]
                torch.distributed.barrier()
                all_gather(
                    dummy_recv_buffer,
                    weight,
                    group=ep_group,
                )
        return

    # Buffers to hold the expert weights during the exchange.
    # NOTE: Currently we assume the same weights across different layers
    # have the same shape.
    weights_buffer = [torch.empty_like(w) for w in first_layer_weights]

    # NOTE(bowen): We need this synchronize to run, but I don't know why.
    # If you figure out the reason, please let me know -- thank you!
    torch.accelerator.synchronize()

    old_global_expert_indices_cpu = old_global_expert_indices.cpu().numpy()
    new_global_expert_indices_cpu = new_global_expert_indices.cpu().numpy()

    for layer_idx in range(num_moe_layers):
        transfer_metadata = move_to_buffer(
            num_local_experts=num_local_physical_experts,
            old_indices=old_global_expert_indices_cpu[layer_idx],
            new_indices=new_global_expert_indices_cpu[layer_idx],
            expert_weights=expert_weights[layer_idx],
            expert_weights_buffers=weights_buffer,
            cuda_stream=None,
            ep_rank=ep_rank,
            communicator=communicator,
        )

        move_from_buffer(
            expert_weights=expert_weights[layer_idx],
            expert_weights_buffers=weights_buffer,
            transfer_metadata=transfer_metadata,
            new_indices=new_global_expert_indices_cpu[layer_idx],
            ep_rank=ep_rank,
        )
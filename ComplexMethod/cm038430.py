def move_to_buffer(
    num_local_experts: int,
    old_indices: np.ndarray,
    new_indices: np.ndarray,
    expert_weights: Sequence[torch.Tensor],
    expert_weights_buffers: Sequence[torch.Tensor],
    cuda_stream: torch.cuda.Stream | None,
    ep_rank: int,
    communicator: EplbCommunicator,
) -> TransferMetadata:
    """
    Rearranges expert weights during EPLB rebalancing.

    Args:
        num_local_experts: Number of local experts.
        old_indices: (num_experts_total,) ndarray of current (old)
            global-to-local expert assignments.
        new_indices: (num_experts_total,) ndarray of desired (new)
            global-to-local assignments after rebalance.
        expert_weights: Original expert weights for the layer.
        expert_weights_buffers: Intermediate buffers (one per tensor).
        cuda_stream: CUDA stream for async copies (can be None for sync mode).
        ep_rank: Rank of this process in expert parallel group.
        communicator: EplbCommunicator instance for P2P communication.

    Returns:
        TransferMetadata: Metadata needed for completing remote weight transfers.
    """
    assert old_indices.shape == new_indices.shape
    recv_primary_mask = np.zeros((num_local_experts,), dtype=np.bool_)
    send_expert_ids = np.full((num_local_experts,), -1, dtype=np.int64)
    send_src_rows = np.full((num_local_experts,), -1, dtype=np.int32)
    recv_expert_ids = np.full((num_local_experts,), -1, dtype=np.int64)
    recv_dst_rows = np.full((num_local_experts,), -1, dtype=np.int32)

    base = ep_rank * num_local_experts
    local_rows = np.arange(num_local_experts, dtype=np.int32)
    local_global = base + local_rows

    old_local_expert_ids = old_indices[local_global]
    new_local_expert_ids = new_indices[local_global]

    # Unchanged mask
    is_unchanged = old_local_expert_ids == new_local_expert_ids

    # Local receive eligibility
    new_valid = new_local_expert_ids != -1
    can_recv_local = np.isin(
        new_local_expert_ids, old_local_expert_ids, assume_unique=False
    )
    is_received_locally = np.logical_or(
        is_unchanged, np.logical_and(new_valid, can_recv_local)
    )

    # Send map: first src row per unique expert present locally in old mapping
    send_count = 0
    valid_old = old_local_expert_ids != -1
    if np.any(valid_old):
        uniq_experts, first_idx = np.unique(
            old_local_expert_ids[valid_old], return_index=True
        )
        filtered_rows = local_rows[valid_old]
        src_rows = filtered_rows[first_idx]
        send_count = int(uniq_experts.shape[0])
        send_expert_ids[:send_count] = uniq_experts
        send_src_rows[:send_count] = src_rows

    # Recv map: primary dst per unique expert needed remotely
    recv_count = 0
    need_recv_mask = np.logical_and(~is_received_locally, new_valid)
    if np.any(need_recv_mask):
        desired_experts = new_local_expert_ids[need_recv_mask]
        desired_dsts = local_rows[need_recv_mask]
        uniq_recv_experts, uniq_indices = np.unique(desired_experts, return_index=True)
        dst_rows = desired_dsts[uniq_indices]
        recv_count = int(uniq_recv_experts.shape[0])
        recv_expert_ids[:recv_count] = uniq_recv_experts
        recv_dst_rows[:recv_count] = dst_rows
        recv_primary_mask[dst_rows] = True

    eligible_local_buffer_mask = np.logical_and(~is_unchanged, is_received_locally)

    # 1. Local moves into tmp buffers
    if bool(eligible_local_buffer_mask.any()) and send_count > 0:
        dest_indices = np.nonzero(eligible_local_buffer_mask)[0].tolist()
        expert_to_src_map = dict(
            zip(send_expert_ids[:send_count], send_src_rows[:send_count])
        )
        for dst in dest_indices:
            expert = new_local_expert_ids[dst]
            src_local = expert_to_src_map.get(expert, -1)
            if src_local != -1:
                with torch.cuda.stream(cuda_stream):
                    for w, b in zip(expert_weights, expert_weights_buffers):
                        b[dst].copy_(w[src_local], non_blocking=True)

    # 2. Post sends
    if send_count > 0:
        experts = send_expert_ids[:send_count]
        srcs = send_src_rows[:send_count]
        order = np.argsort(experts, kind="stable")
        experts = experts[order]
        srcs = srcs[order]

        send_map, recv_map = get_ep_ranks_with_experts_batch(
            experts,
            num_local_experts,
            old_indices,
            new_indices,
        )

        for expert, src in zip(experts.tolist(), srcs.tolist()):
            ranks_to_send = send_map[expert]
            ranks_to_recv = recv_map[expert]
            if not ranks_to_send or not ranks_to_recv:
                continue
            num_dst_per_sender = len(ranks_to_recv) // len(ranks_to_send)
            sender_pos = ranks_to_send.index(ep_rank)
            recv_begin = sender_pos * num_dst_per_sender
            recv_end = recv_begin + num_dst_per_sender
            recv_ranks = ranks_to_recv[recv_begin:recv_end]
            remainder_start = len(ranks_to_send) * num_dst_per_sender
            recver_pos = remainder_start + sender_pos
            if recver_pos < len(ranks_to_recv):
                recv_ranks.append(ranks_to_recv[recver_pos])
            for dst in recv_ranks:
                for w in expert_weights:
                    communicator.add_send(w[src], dst)

    # 3. Post recvs
    if recv_count > 0:
        experts = recv_expert_ids[:recv_count]
        dsts = recv_dst_rows[:recv_count]
        order = np.argsort(experts, kind="stable")
        experts = experts[order]
        dsts = dsts[order]

        send_map, recv_map = get_ep_ranks_with_experts_batch(
            experts,
            num_local_experts,
            old_indices,
            new_indices,
        )

        for expert, dst in zip(experts.tolist(), dsts.tolist()):
            ranks_to_send = send_map[expert]
            ranks_to_recv = recv_map[expert]
            if not ranks_to_send or not ranks_to_recv:
                continue
            num_dst_per_sender = len(ranks_to_recv) // len(ranks_to_send)
            recver_pos = ranks_to_recv.index(ep_rank)
            remainder_start = len(ranks_to_send) * num_dst_per_sender
            if recver_pos < remainder_start:
                src = ranks_to_send[recver_pos // num_dst_per_sender]
            else:
                src = ranks_to_send[recver_pos - remainder_start]
            for b in expert_weights_buffers:
                communicator.add_recv(b[dst], src)

    # 4. Execute the P2P operations. The real communication happens here.
    communicator.execute()
    # wait for the communication to finish
    return TransferMetadata(
        is_unchanged=is_unchanged,
        is_received_locally=is_received_locally,
        recv_primary_mask=recv_primary_mask,
        recv_count=recv_count,
        recv_expert_ids=recv_expert_ids,
        recv_dst_rows=recv_dst_rows,
    )
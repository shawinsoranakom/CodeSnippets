def broadcast_expert_mapping(
    physical_to_logical: torch.Tensor | None,
    num_local_physical_experts: int | None,
    num_logical_experts: int | None,
    dp_group: StatelessGroupCoordinator,
    device: torch.device,
    src_rank: int = 0,
) -> tuple[torch.Tensor, int, int]:
    if dp_group.rank_in_group == src_rank:
        assert physical_to_logical is not None
        assert num_local_physical_experts is not None
        assert num_logical_experts is not None
        assert physical_to_logical.dtype == torch.int64
        shape_tensor = torch.tensor(
            list(physical_to_logical.shape), dtype=torch.int64, device="cpu"
        )
        metadata_tensor = torch.tensor(
            [num_local_physical_experts, num_logical_experts],
            dtype=torch.int64,
            device="cpu",
        )
    else:
        shape_tensor = torch.empty(2, dtype=torch.int64, device="cpu")
        metadata_tensor = torch.empty(2, dtype=torch.int64, device="cpu")

    shape_tensor = dp_group.tcp_store_group.broadcast(shape_tensor, src_rank)
    metadata_tensor = dp_group.tcp_store_group.broadcast(metadata_tensor, src_rank)

    if dp_group.rank_in_group != src_rank:
        assert device is not None
        physical_to_logical = torch.empty(
            tuple(shape_tensor.tolist()),
            dtype=torch.int64,
            device=device,
        )

    assert physical_to_logical is not None
    physical_to_logical = dp_group.broadcast(physical_to_logical, src_rank)
    num_local_physical_experts = int(metadata_tensor[0].item())
    num_logical_experts = int(metadata_tensor[1].item())

    return physical_to_logical, num_local_physical_experts, num_logical_experts
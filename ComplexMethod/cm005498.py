def _block_diag_3d(tensors: list[torch.Tensor]) -> torch.Tensor:
    if len(tensors) < 2:
        raise ValueError(f"_block_diag_3d expects at least 2 tensors, got {len(tensors)}")

    if any(t.dim() != 3 for t in tensors):
        raise ValueError("_block_diag_3d expects all tensors to be 3d.")

    num_experts = tensors[0].shape[0]
    if any(t.shape[0] != num_experts for t in tensors):
        raise ValueError("All tensors passed to _block_diag_3d must have the same number of experts.")

    lora_b_block_diag = []
    for i in range(num_experts):
        lora_b_block_diag.append(torch.block_diag(*[tensor[i] for tensor in tensors]))
    return torch.stack(lora_b_block_diag, dim=0)
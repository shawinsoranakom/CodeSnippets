def compare_top_k_results(
    logits: torch.Tensor,
    cuda_indices: torch.Tensor,
    torch_indices: torch.Tensor,
    row_starts: torch.Tensor,
    row_ends: torch.Tensor,
    top_k: int,
    tolerance: float = 1e-5,
) -> bool:
    """
    Compare results from CUDA top_k_per_row with torch.topk.
    Both results should be sorted and contain the same top-k elements.
    """
    num_rows = cuda_indices.shape[0]

    for row_idx in range(num_rows):
        # Get valid elements using row boundaries
        row_start = row_starts[row_idx].item()
        row_end = row_ends[row_idx].item()
        row_length = row_end - row_start
        num_valid = min(top_k, row_length)
        cuda_row_indices = cuda_indices[row_idx][:num_valid].cpu()
        torch_row_indices = torch_indices[row_idx][:num_valid].cpu()

        # Compare the sets of indices first
        cuda_set = set(cuda_row_indices.tolist())
        torch_set = set(torch_row_indices.tolist())
        if cuda_set == torch_set:
            continue

        # Any difference in elements, compare the values
        logits_row = logits[row_idx]
        cuda_row_values = [logits_row[i] for i in cuda_row_indices]
        torch_row_values = [logits_row[i] for i in torch_row_indices]

        cuda_only_values, torch_only_values = [], []
        for idx in cuda_set - torch_set:
            cuda_pos = (cuda_row_indices == idx).nonzero(as_tuple=True)[0]
            cuda_only_values.append(cuda_row_values[cuda_pos[0]])

        for idx in torch_set - cuda_set:
            torch_pos = (torch_row_indices == idx).nonzero(as_tuple=True)[0]
            torch_only_values.append(torch_row_values[torch_pos[0]])

        if len(cuda_only_values) != len(torch_only_values):
            return False
        if not torch.allclose(
            torch.tensor(cuda_only_values),
            torch.tensor(torch_only_values),
            rtol=tolerance,
            atol=tolerance,
        ):
            return False

    return True
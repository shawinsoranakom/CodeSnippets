def process_patch_lengths(patch_lengths: torch.Tensor, max_patch_length: int | None) -> torch.Tensor:
    """
    Splits patch lengths into smaller segments if they exceed `max_patch_length`.
    Pads the result to uniform length across the batch.

    Args:
        patch_lengths (torch.Tensor): [batch_size, num_patches] tensor of patch lengths.
        max_patch_length (int, optional): Maximum allowed length per patch.

    Returns:
        torch.Tensor: [batch_size, max_len] tensor of split and padded patch lengths.
    """
    if max_patch_length is None:
        return patch_lengths

    batch_size = patch_lengths.size(0)
    processed = []

    for seq in patch_lengths:
        splits = []
        for length in seq[seq > 0]:
            length = length.item()
            full_chunks, remainder = divmod(length, max_patch_length)
            splits.extend([max_patch_length] * full_chunks)
            if remainder:
                splits.append(remainder)
        processed.append(splits)

    # Find max length to pad to
    max_len = max(len(splits) for splits in processed)
    padded = torch.zeros((batch_size, max_len), dtype=patch_lengths.dtype, device=patch_lengths.device)

    for i, splits in enumerate(processed):
        if splits:
            padded[i, : len(splits)] = torch.tensor(splits, dtype=patch_lengths.dtype, device=patch_lengths.device)

    # Trim zero columns
    if (padded != 0).any(dim=0).sum() < padded.shape[1]:
        last_nonzero = (padded != 0).any(dim=0).nonzero().max().item() + 1
        padded = padded[:, :last_nonzero]

    return padded
def _count_audio_tokens_from_mask(
    feature_attention_mask: torch.Tensor | list[torch.Tensor],
    chunk_counts: torch.Tensor | list[torch.Tensor] | list[int] | None,
    item_idx: int,
) -> int:
    if chunk_counts is not None:
        if isinstance(chunk_counts, torch.Tensor):
            counts = chunk_counts.tolist()
        elif chunk_counts and isinstance(chunk_counts[0], torch.Tensor):
            counts = [count.item() for count in chunk_counts]
        else:
            counts = chunk_counts

        start_idx = sum(counts[:item_idx])
        count = counts[item_idx]
        end_idx = start_idx + count

        if isinstance(feature_attention_mask, list):
            sample_mask = feature_attention_mask[start_idx:end_idx]
            if len(sample_mask) == 0:
                raise ValueError("Expected non-empty audio mask slice.")
            if isinstance(sample_mask[0], torch.Tensor):
                sample_mask = torch.stack(sample_mask)
            else:
                sample_mask = torch.tensor(sample_mask)
        else:
            sample_mask = feature_attention_mask[start_idx:end_idx]
    else:
        if isinstance(feature_attention_mask, list):
            sample_mask = feature_attention_mask[item_idx]
        else:
            sample_mask = feature_attention_mask[item_idx]

    if sample_mask.ndim == 1:
        sample_input_lengths = sample_mask.sum().unsqueeze(0)
    else:
        # Match the HF processor, which derives placeholder lengths from the
        # total pre-encoder feature length for each original audio sample.
        sample_input_lengths = sample_mask.sum().reshape(1)

    post_lengths = _get_audio_post_pool_output_lengths(
        sample_input_lengths.to(torch.long)
    )
    return int(post_lengths[0].item())
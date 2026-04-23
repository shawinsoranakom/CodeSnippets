def is_attention_mask_causal(attention_mask):
    """
    Check if an attention mask is causal (compatible with causal attention).

    Context parallelism only supports causal attention patterns. This function
    checks if the provided attention mask is compatible.

    Args:
        attention_mask (`torch.Tensor`): The attention mask to check.

    Returns:
        `bool`: True if the mask is causal or compatible with causal attention.
    """
    if attention_mask is None:
        return True  # No mask is considered causal (model uses default causal masking)

    # Handle different mask dimensions
    if attention_mask.dim() == 2:
        # (batch_size, seq_len) - standard padding mask, compatible with causal attention
        return True
    elif attention_mask.dim() in [3, 4]:
        # (batch_size, seq_len, seq_len) or (batch_size, num_heads, seq_len, seq_len)
        # Check if it's lower triangular (causal)
        seq_len = attention_mask.shape[-1]
        if seq_len <= 1:
            return True  # Single token or empty is always causal

        # Take first batch and head (if 4D) for checking pattern
        if attention_mask.dim() == 4:
            mask = attention_mask[0, 0]  # First batch, first head
        else:
            mask = attention_mask[0]  # First batch

        # Check if upper triangular part is masked (should be 0 or very negative for causal)
        upper_triangular = torch.triu(mask, diagonal=1)

        # For causal masks, upper triangular should be 0 or very negative (like -inf)
        # Use a reasonable threshold to handle float precision issues
        is_causal = torch.all(upper_triangular <= 1e-6) or torch.all(upper_triangular < -1e4)
        return is_causal.item() if isinstance(is_causal, torch.Tensor) else is_causal

    # For unknown dimensions, be conservative and reject
    return False
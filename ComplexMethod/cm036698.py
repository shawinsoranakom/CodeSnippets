def ref_masked_attention(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    is_causal: bool = True,
    sliding_window_q: int | None = None,
    sliding_window_k: int | None = None,
) -> torch.Tensor:
    """Reference implementation using PyTorch SDPA."""
    # q, k, v: [total_tokens, num_heads, head_dim]
    # SDPA expects [batch, num_heads, seq_len, head_dim]

    total_tokens = q.shape[0]

    # Add batch dimension and transpose
    q = q.unsqueeze(0).transpose(1, 2)  # [1, num_heads, total_tokens, head_dim]
    k = k.unsqueeze(0).transpose(1, 2)  # [1, num_heads, total_tokens, head_dim]
    v = v.unsqueeze(0).transpose(1, 2)  # [1, num_heads, total_tokens, head_dim]

    # Create attention mask if needed
    attn_mask = None
    use_causal = is_causal

    # If we have sliding window or need custom masking, create explicit mask
    sliding_window_q = sliding_window_q if sliding_window_q is not None else 0
    sliding_window_k = sliding_window_k if sliding_window_k is not None else 0
    if (sliding_window_q > 0) or (sliding_window_k > 0):
        # Position indices
        pos_q = torch.arange(total_tokens, device=q.device).unsqueeze(1)
        pos_k = torch.arange(total_tokens, device=q.device).unsqueeze(0)

        # Start with valid mask (False = no masking)
        mask = torch.ones(
            (total_tokens, total_tokens), dtype=torch.bool, device=q.device
        )

        # Apply causal mask
        if is_causal:
            mask = mask & (pos_q >= pos_k)

        # Apply sliding window masks
        sliding_window_mask = torch.ones_like(mask)
        if sliding_window_q > 0:
            sliding_window_mask &= pos_q - pos_k <= sliding_window_q

        if sliding_window_k > 0:
            sliding_window_mask &= pos_k - pos_q <= sliding_window_k

        mask = mask & sliding_window_mask

        attn_mask = torch.where(mask, 0.0, float("-inf")).to(q.dtype)
        use_causal = False  # Don't use is_causal when providing explicit mask

    # Use SDPA
    output = F.scaled_dot_product_attention(
        q, k, v, attn_mask=attn_mask, is_causal=use_causal, dropout_p=0.0
    )

    # Convert back to original shape: [total_tokens, num_heads, head_dim]
    output = output.transpose(1, 2).squeeze(0)

    return output
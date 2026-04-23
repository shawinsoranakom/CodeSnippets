def ref_masked_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    scale: float,
    custom_mask: torch.Tensor | None = None,
    q_seq_lens: list | None = None,
    kv_seq_lens: list | None = None,
) -> torch.Tensor:
    """
    "Golden" masked attention reference. Supports two types of masking:

    * Basic attention mask, utilizing {q,kv}_seq_lens args to mask out
      padding elements
    * Custom attention mask, which can force an arbitrary mask tensor, i.e.
      causal

    Arguments:

    * query: batch_size x q_padded_seq_len x num_heads x head_size
    * key: batch_size x kv_padded_seq_len x num_heads x head_size
    * value: batch_size x kv_padded_seq_len x num_heads x head_size
    * scale: Attention scale factor
    * custom_mask: custom attention mask; good place to inject a causal
      attention mask
    * q_seq_lens: list of unpadded query seq_lens for each batch index
    * kv_seq_lens: list of unpadded key/value seq_lens for each batch index

    Returns:

    * Attention result, batch_size x q_padded_seq_len x num_heads x head_size
    """

    assert q_seq_lens is not None
    assert kv_seq_lens is not None

    batch_size = query.shape[0]
    assert len(q_seq_lens) == batch_size
    assert len(kv_seq_lens) == batch_size

    attn_weights = scale * torch.einsum("bqhd,bkhd->bhqk", query, key).float()

    # Basic attention mask, derived from seq lens
    if (q_seq_lens is not None) or (kv_seq_lens is not None):
        attn_mask = torch.zeros_like(attn_weights)
        if q_seq_lens is not None:
            for bdx, plen in enumerate(q_seq_lens):
                attn_mask[bdx, :, plen:, :] = -torch.inf
        if kv_seq_lens is not None:
            for bdx, plen in enumerate(kv_seq_lens):
                attn_mask[bdx, :, :, plen:] = -torch.inf

        attn_weights = attn_weights + attn_mask.float()

    # Custom attention mask
    if custom_mask is not None:
        attn_weights = attn_weights + custom_mask.float()

    attn_weights = torch.softmax(attn_weights, dim=-1).to(value.dtype)
    out = torch.einsum("bhqk,bkhd->bqhd", attn_weights, value)
    return out
def make_qkv(
    batch_size: int,
    max_q_seq_len: int,
    max_kv_seq_len: int | None,
    num_heads: int,
    head_size: int,
    device: torch.device | str,
    force_kv_seq_lens: list[int] | None = None,
    attn_type: AttentionType = AttentionType.ENCODER_DECODER,
    force_max_len: bool = False,
) -> tuple[QKVInputs, QKVInputs, QKVInputs]:
    """
    Construct QKV test tensors for self- and cross-attention.

    Generates three query/key/value triplets:

    * "Baseline" query/key/value (for input to reference attention function)
    * "Prefill" query/key/value (last sequence offset zero'd out, for use as
      input to prefill kernel)
    * "Decode" query/key/value (only the last sequence offset  from baseline,
      for use as input to decode kernel)

    Each Q/K/V triplet is associated with a list of q seqlens and a list of k/v
    seqlens

    Arguments:

    * batch_size
    * max_q_seq_len: max query seq len
    * max_kv_seq_len: max key/value seq len
    * num_heads
    * head_size
    * is_encoder_decoder_attn: if True, query seqlen may differ from
      key/value seqlen (as is often the case for cross-attention);
      o/w, query/key/value seqlens match at each batch index
      (max_kv_seq_len is unused)
    * force_kv_seq_lens: if not None, overrides kv sequence lengths
    * attn_type: encoder, decoder self, or enc/dec cross attention
    * force_max_len: if True, all query seqlens are max_q_seq_len; o/w query
      seqlens are random in [2,max_q_seq_lens]. Same for key/value seqlens
      and max_kv_seq_len, unless forced by is_encoder_decoder_attn=False
    * device: CPU or CUDA device

    Returns:

    * Overall QKVInputs structure (containing full unpacked Q/K/V tensors)
    * Prefill QKVInputs structure (containing all but the last sequence offset)
    * Decode QKVInputs structure (containing all only the last sequence offset)
    """

    if force_max_len:
        q_seq_lens = [max_q_seq_len for _ in range(batch_size)]
    else:
        q_seq_lens = [random.randint(2, max_q_seq_len) for _ in range(batch_size)]
    kv_seq_lens = None
    if force_kv_seq_lens is not None:
        kv_seq_lens = force_kv_seq_lens
    elif attn_type != AttentionType.ENCODER_DECODER:
        # K,V seq lens match Q for self-attention
        kv_seq_lens = q_seq_lens
    else:
        # K,V seq lens are distinct from Q seq lens & random
        assert max_kv_seq_len is not None
        if force_max_len:
            kv_seq_lens = [max_kv_seq_len] * batch_size
        else:
            kv_seq_lens = [random.randint(2, max_kv_seq_len) for _ in range(batch_size)]

    query = torch.rand((batch_size, max_q_seq_len, num_heads, head_size)).to(device)
    key = torch.rand((batch_size, max_kv_seq_len, num_heads, head_size)).to(device)
    value = torch.rand((batch_size, max_kv_seq_len, num_heads, head_size)).to(device)

    prefill_query = torch.zeros((batch_size, max_q_seq_len, num_heads, head_size)).to(
        device
    )
    prefill_key = torch.zeros((batch_size, max_kv_seq_len, num_heads, head_size)).to(
        device
    )
    prefill_value = torch.zeros((batch_size, max_kv_seq_len, num_heads, head_size)).to(
        device
    )

    decode_query = torch.zeros((batch_size, 1, num_heads, head_size)).to(device)
    decode_key = torch.zeros((batch_size, 1, num_heads, head_size)).to(device)
    decode_value = torch.zeros((batch_size, 1, num_heads, head_size)).to(device)

    for bdx, (q_seq_len, kv_seq_len) in enumerate(zip(q_seq_lens, kv_seq_lens)):
        query[bdx, q_seq_len:, :, :] = 0
        key[bdx, kv_seq_len:, :, :] = 0
        value[bdx, kv_seq_len:, :, :] = 0

        prefill_query[bdx, 0 : (q_seq_len - 1), :, :] = query[
            bdx, 0 : (q_seq_len - 1), :, :
        ]
        prefill_key[bdx, 0 : (kv_seq_len - 1), :, :] = key[
            bdx, 0 : (kv_seq_len - 1), :, :
        ]
        prefill_value[bdx, 0 : (kv_seq_len - 1), :, :] = value[
            bdx, 0 : (kv_seq_len - 1), :, :
        ]

        decode_query[bdx, :, :, :] = query[bdx, (q_seq_len - 1) : q_seq_len, :, :]
        decode_key[bdx, :, :, :] = key[bdx, (kv_seq_len - 1) : kv_seq_len, :, :]
        decode_value[bdx, :, :, :] = value[bdx, (kv_seq_len - 1) : kv_seq_len, :, :]

    prefill_q_seq_lens = [plen - 1 for plen in q_seq_lens]
    prefill_kv_seq_lens = [plen - 1 for plen in kv_seq_lens]

    decode_q_seq_lens = [1 for _ in q_seq_lens]
    decode_kv_seq_lens = [1 for _ in kv_seq_lens]

    return (
        QKVInputs(
            query,  # Overall QKV inputs
            key,
            value,
            q_seq_lens,
            kv_seq_lens,
        ),
        QKVInputs(
            prefill_query,  # Prefill subset of QKV sequences
            prefill_key,
            prefill_value,
            prefill_q_seq_lens,
            prefill_kv_seq_lens,
        ),
        QKVInputs(
            decode_query,  # Decode subset of KV sequences
            decode_key,
            decode_value,
            decode_q_seq_lens,
            decode_kv_seq_lens,
        ),
    )
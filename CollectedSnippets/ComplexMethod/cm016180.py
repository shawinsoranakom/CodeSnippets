def generate_block_mask(attn_type: str, shape: tuple[int, ...]):
    B, Hq, M, Hkv, N, D = shape
    is_decoding = M == 1

    def causal(b, h, m, n):
        return m >= n

    def gen_offset(off):
        def offset(b, h, m, n):
            return m + off >= n

        return offset

    from attn_gym.masks import (
        generate_doc_mask_mod,
        generate_prefix_lm_mask,
        generate_sliding_window,
    )
    from attn_gym.masks.document_mask import length_to_offsets

    def generate_random_lengths(total_length, num_documents):
        # Initialize all lengths to 1 to ensure each document has at least one token
        lengths = [1] * num_documents
        remaining_length = total_length - num_documents

        # Randomly distribute the remaining length
        for _ in range(remaining_length):
            index = random.randint(0, num_documents - 1)
            lengths[index] += 1
        return lengths

    mask_mod_kwargs = {}

    if attn_type == "document_mask" and is_decoding:
        raise AssertionError(
            "document_mask attention type is not supported in decoding mode"
        )
    if attn_type == "document_mask":
        random.seed(0)
        lengths = generate_random_lengths(N * B, B)
        mask_mod_kwargs = dict(offsets=length_to_offsets(lengths, "cuda"))

    mask_mod_dict = {
        "noop": None,
        "causal": causal,
        "rel": None,
        "head_bias": None,
        "alibi": causal,
        "sliding_window": generate_sliding_window(sliding_window_size),
        "document_mask": partial(generate_doc_mask_mod, mask_mod=causal),
        "prefix_lm": generate_prefix_lm_mask(prefix_length),
        "softcap": causal,
    }

    mask_mod = mask_mod_dict[attn_type]

    if mask_mod_kwargs:
        mask_mod = mask_mod(**mask_mod_kwargs)

    if is_decoding and mask_mod:
        cached_seq_len = torch.tensor(N // 2).to("cuda")

        def decoding_w_cached_seq_len(b, h, m, n):
            return mask_mod(b, h, m + cached_seq_len, n)

        new_mask_mod = decoding_w_cached_seq_len
    else:
        new_mask_mod = mask_mod

    mask_shape = (1, 1, M, N) if attn_type != "document_mask" else (1, 1, M * B, N * B)
    compiled_block_mask = torch.compile(create_block_mask)
    if new_mask_mod:
        block_mask = compiled_block_mask(new_mask_mod, *mask_shape, "cuda")
    else:
        block_mask = compiled_block_mask(noop_mask, *mask_shape, "cuda")
    return block_mask, mask_mod_kwargs
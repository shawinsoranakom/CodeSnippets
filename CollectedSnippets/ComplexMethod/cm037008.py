def generate_fp8_expand_data(
    batches: int,
    hidden_size: int,
    num_loras: int,
    rank: int,
    seq_length: int,
    nslices: int,
    dtype: torch.dtype,
    device: str,
    quant_mode: str,  # "per_tensor", "per_channel", "blockwise"
    group_k: int = 128,
    group_n: int = 128,
):
    """Generate test data for FP8 expand kernel (w8a8).

    Expand: output += input @ lora_b^T
    input: (nslices, num_tokens, rank) -> quantized to FP8 (activations)
    lora_b: (num_loras, hidden_size, rank) -> quantized to FP8 (weights)

    In w8a8 mode, both activations and weights are FP8.
    Returns bf16 reference tensors, FP8 quantized tensors with scales,
    and dequantized bf16 tensors for accurate reference computation.
    """
    seq_len_tensor = torch.randint(seq_length, seq_length + 1, (batches,)).to(device)
    b_seq_start_loc = torch.cumsum(
        torch.tensor([0] + seq_len_tensor[:-1].tolist(), dtype=torch.long),
        dim=0,
    ).to(device)
    total_tokens = seq_len_tensor.sum().item()

    # Generate bf16 input (shrink output) and quantize to FP8
    inputs_bf16 = torch.randn(nslices, total_tokens, rank, dtype=dtype, device=device)

    # Quantize input to FP8 and dequantize back for reference
    inputs_2d_all = inputs_bf16.reshape(-1, rank)
    if quant_mode == "blockwise":
        # For blockwise, the kernel indexes a_scale by token id (0..total_tokens-1)
        # shared across slices. Compute shared scale across slices, then quantize.
        # First compute per-token-per-block scale across all slices
        n_blocks_k = math.ceil(rank / group_k)
        a_scale = torch.zeros(
            total_tokens, n_blocks_k, dtype=torch.float32, device=device
        )
        for m in range(total_tokens):
            for bk in range(n_blocks_k):
                k_start = bk * group_k
                k_end = min(k_start + group_k, rank)
                # Max across all slices for this token and block
                block_amax = torch.tensor(0.0, device=device)
                for s in range(nslices):
                    block = inputs_bf16[s, m, k_start:k_end].float()
                    block_amax = torch.max(
                        block_amax, block.abs().max().clamp(min=1e-12)
                    )
                a_scale[m, bk] = (block_amax / FP8_MAX).to(torch.float32)

        # Quantize all slices with the shared scale
        inputs_fp8_list = []
        inputs_dequant_list = []
        for s in range(nslices):
            slice_2d = inputs_bf16[s]  # (total_tokens, rank)
            fp8_slice = torch.zeros_like(slice_2d, dtype=FP8_DTYPE)
            dequant_slice = torch.zeros_like(slice_2d)
            for m in range(total_tokens):
                for bk in range(n_blocks_k):
                    k_start = bk * group_k
                    k_end = min(k_start + group_k, rank)
                    block = slice_2d[m, k_start:k_end].float()
                    s_val = a_scale[m, bk]
                    fp8_slice[m, k_start:k_end] = (
                        (block / s_val).clamp(FP8_MIN, FP8_MAX).to(FP8_DTYPE)
                    )
                    dequant_slice[m, k_start:k_end] = (
                        fp8_slice[m, k_start:k_end].float() * s_val.float()
                    ).to(dtype)
            inputs_fp8_list.append(fp8_slice)
            inputs_dequant_list.append(dequant_slice)
        inputs_fp8 = torch.stack(inputs_fp8_list, dim=0)
        inputs_dequant = torch.stack(inputs_dequant_list, dim=0)
    elif quant_mode == "per_tensor":
        # Per-tensor: kernel loads a single scalar from a_scale_ptr
        inputs_fp8_2d, a_scale = quantize_to_fp8_per_tensor(inputs_2d_all)
        inputs_dequant_2d = dequantize_fp8_per_tensor(
            inputs_fp8_2d,
            a_scale,
            output_dtype=dtype,
        )
        inputs_fp8 = inputs_fp8_2d.reshape(nslices, total_tokens, rank)
        inputs_dequant = inputs_dequant_2d.reshape(nslices, total_tokens, rank)
    else:
        # per_channel: kernel loads per-token a_scale via ram indexing.
        # The kernel uses the same a_scale for all slices (indexed by token
        # id 0..total_tokens-1), so we compute a shared per-token scale
        # across all slices, then quantize each slice with that shared scale.
        per_slice_views = [inputs_bf16[s] for s in range(nslices)]
        # (nslices, total_tokens, rank) -> max across slices per token
        stacked = torch.stack(per_slice_views, dim=0)  # (nslices, tokens, rank)
        amax = stacked.abs().float().amax(dim=(0, 2), keepdim=False).clamp(min=1e-12)
        # amax shape: (total_tokens,)
        a_scale = (amax / FP8_MAX).to(torch.float32).unsqueeze(1)  # (tokens, 1)
        # Quantize all slices with the shared scale
        inputs_fp8_2d = (
            (inputs_2d_all.float() / a_scale.repeat(nslices, 1))
            .clamp(FP8_MIN, FP8_MAX)
            .to(FP8_DTYPE)
        )
        inputs_dequant_2d = (
            inputs_fp8_2d.float() * a_scale.repeat(nslices, 1).float()
        ).to(dtype)
        inputs_fp8 = inputs_fp8_2d.reshape(nslices, total_tokens, rank)
        inputs_dequant = inputs_dequant_2d.reshape(nslices, total_tokens, rank)

    # Generate bf16 LoRA B weights
    lora_b_weights_bf16 = []
    for _ in range(nslices):
        lora_b_weights_bf16.append(
            torch.randn(num_loras, hidden_size, rank, dtype=dtype, device=device)
        )

    # Quantize LoRA B weights to FP8 and dequantize back for reference
    b_scales = []
    lora_b_weights_fp8 = []
    lora_b_weights_dequant = []
    for w in lora_b_weights_bf16:
        if quant_mode == "per_tensor":
            w_fp8, w_scale = quantize_to_fp8_per_tensor(w)
            w_dequant = dequantize_fp8_per_tensor(w_fp8, w_scale, output_dtype=dtype)
            w_scale = w_scale.expand(num_loras).contiguous()
            lora_b_weights_fp8.append(w_fp8)
            b_scales.append(w_scale)
            lora_b_weights_dequant.append(w_dequant)
        elif quant_mode == "per_channel":
            # Per-channel along hidden_size dim: scale (num_loras, hidden_size)
            w_fp8, w_scale = quantize_to_fp8_per_channel(w, channel_dim=1)
            w_dequant = dequantize_fp8_per_channel(
                w_fp8,
                w_scale,
                channel_dim=1,
                output_dtype=dtype,
            )
            lora_b_weights_fp8.append(w_fp8)
            b_scales.append(w_scale)
            lora_b_weights_dequant.append(w_dequant)
        elif quant_mode == "blockwise":
            w_fp8, w_scale = quantize_to_fp8_blockwise(
                w, group_n=group_n, group_k=group_k
            )
            w_dequant = dequantize_fp8_blockwise(
                w_fp8,
                w_scale,
                group_n=group_n,
                group_k=group_k,
                output_dtype=dtype,
            )
            lora_b_weights_fp8.append(w_fp8)
            b_scales.append(w_scale)
            lora_b_weights_dequant.append(w_dequant)

    # Output tensor (initialized randomly for add_inputs)
    out_tensor = torch.randn(
        total_tokens, hidden_size * nslices, dtype=dtype, device=device
    )
    ref_out_tensor = out_tensor.clone()

    # Token-to-lora mapping
    lora_indices_tensor = torch.randint(0, max(num_loras - 1, 1), (batches,)).to(device)
    token_lora_mapping = torch.zeros(total_tokens, dtype=torch.long, device=device)
    current_offset = 0
    for b_id in range(batches):
        lora_index = lora_indices_tensor[b_id]
        sl = seq_len_tensor[b_id].item()
        token_lora_mapping[current_offset : current_offset + sl] = lora_index
        current_offset += sl

    return {
        "inputs_bf16": inputs_bf16,
        "inputs_fp8": inputs_fp8,
        "inputs_dequant": inputs_dequant,
        "a_scale": a_scale,
        "lora_b_bf16": lora_b_weights_bf16,
        "lora_b_fp8": lora_b_weights_fp8,
        "lora_b_dequant": lora_b_weights_dequant,
        "b_scales": b_scales,
        "out_tensor": out_tensor,
        "ref_out_tensor": ref_out_tensor,
        "token_lora_mapping": token_lora_mapping,
        "seq_len_tensor": seq_len_tensor,
        "b_seq_start_loc": b_seq_start_loc,
        "lora_indices_tensor": lora_indices_tensor,
        "total_tokens": total_tokens,
    }
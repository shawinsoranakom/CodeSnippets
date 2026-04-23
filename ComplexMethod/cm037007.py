def generate_fp8_shrink_data(
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
    """Generate test data for FP8 shrink kernel.

    Shrink: output = input @ lora_a^T * scaling
    input: (num_tokens, hidden_size) -> quantized to FP8
    lora_a: (num_loras, rank, hidden_size) -> quantized to FP8

    Returns bf16 reference tensors, FP8 quantized tensors with scales,
    and dequantized bf16 tensors for accurate reference computation.
    """
    seq_len_tensor = torch.randint(seq_length, seq_length + 1, (batches,)).to(device)
    b_seq_start_loc = torch.cumsum(
        torch.tensor([0] + seq_len_tensor[:-1].tolist(), dtype=torch.long),
        dim=0,
    ).to(device)
    total_tokens = seq_len_tensor.sum().item()

    # Generate bf16 reference data
    inputs_bf16 = torch.randn(total_tokens, hidden_size, dtype=dtype, device=device)

    lora_a_weights_bf16 = []
    for _ in range(nslices):
        lora_a_weights_bf16.append(
            torch.randn(num_loras, rank, hidden_size, dtype=dtype, device=device)
        )

    # Quantize inputs to FP8 and dequantize back for reference
    if quant_mode == "blockwise":
        inputs_fp8, a_scale = quantize_to_fp8_blockwise(
            inputs_bf16, group_n=1, group_k=group_k
        )
        inputs_dequant = dequantize_fp8_blockwise(
            inputs_fp8,
            a_scale,
            group_n=1,
            group_k=group_k,
            output_dtype=dtype,
        )
    elif quant_mode == "per_tensor":
        # Per-tensor: kernel loads a single scalar from a_scale_ptr
        inputs_fp8, a_scale = quantize_to_fp8_per_tensor(inputs_bf16)
        inputs_dequant = dequantize_fp8_per_tensor(
            inputs_fp8,
            a_scale,
            output_dtype=dtype,
        )
    else:
        # per_channel: kernel loads per-token a_scale via ram indexing
        inputs_fp8, a_scale = quantize_to_fp8_per_token(inputs_bf16)
        inputs_dequant = dequantize_fp8_per_token(
            inputs_fp8,
            a_scale,
            output_dtype=dtype,
        )

    # Quantize lora_a weights to FP8 and dequantize back for reference
    b_scales = []
    lora_a_weights_fp8 = []
    lora_a_weights_dequant = []
    for w in lora_a_weights_bf16:
        if quant_mode == "per_tensor":
            w_fp8, w_scale = quantize_to_fp8_per_tensor(w)
            w_dequant = dequantize_fp8_per_tensor(w_fp8, w_scale, output_dtype=dtype)
            # Scale shape: (1,) -> need (num_loras,) for the kernel
            w_scale = w_scale.expand(num_loras).contiguous()
            lora_a_weights_fp8.append(w_fp8)
            b_scales.append(w_scale)
            lora_a_weights_dequant.append(w_dequant)
        elif quant_mode == "per_channel":
            # Per-channel along rank dim: scale shape (num_loras, rank)
            w_fp8, w_scale = quantize_to_fp8_per_channel(w, channel_dim=1)
            w_dequant = dequantize_fp8_per_channel(
                w_fp8,
                w_scale,
                channel_dim=1,
                output_dtype=dtype,
            )
            lora_a_weights_fp8.append(w_fp8)
            b_scales.append(w_scale)
            lora_a_weights_dequant.append(w_dequant)
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
            lora_a_weights_fp8.append(w_fp8)
            b_scales.append(w_scale)
            lora_a_weights_dequant.append(w_dequant)

    # Output tensor (float32 for shrink)
    out_tensor = torch.zeros(
        nslices, total_tokens, rank, dtype=torch.float32, device=device
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
        "lora_a_bf16": lora_a_weights_bf16,
        "lora_a_fp8": lora_a_weights_fp8,
        "lora_a_dequant": lora_a_weights_dequant,
        "a_scale": a_scale,
        "b_scales": b_scales,
        "out_tensor": out_tensor,
        "ref_out_tensor": ref_out_tensor,
        "token_lora_mapping": token_lora_mapping,
        "seq_len_tensor": seq_len_tensor,
        "b_seq_start_loc": b_seq_start_loc,
        "lora_indices_tensor": lora_indices_tensor,
        "total_tokens": total_tokens,
    }
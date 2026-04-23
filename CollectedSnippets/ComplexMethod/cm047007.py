def fast_linear_forward(proj, X, temp_lora = None, out = None):
    W, W_quant, lora_A, lora_B, lora_S, bias = get_lora_parameters_bias(proj)
    bsz, q_len, in_dim = X.shape
    if q_len != 1:
        return matmul_lora(X, W, W_quant, lora_A, lora_B, lora_S)

    if W_quant is None:
        out = torch_matmul(X, W.t(), out = out)
    elif W.dtype == torch.float8_e4m3fn:
        out = fp8_linear(X, W, W_quant, bias)
    elif bsz == 1 and q_len == 1:
        out = fast_gemv(X, W, W_quant, out = out)
    else:
        W = fast_dequantize(W.t(), W_quant, use_global_buffer = True)
        out = torch_matmul(X, W, out = out)

    # Add in LoRA weights
    if lora_A is not None:
        out_dim = out.shape[2]
        dtype = X.dtype

        if not hasattr(lora_A, "_fast_lora"):
            lora_A._fast_lora = lora_A.to(dtype)
            lora_B._fast_lora = lora_B.to(dtype)

        if bsz == 1:
            out = out.view(out_dim)
            temp_lora = torch_mv(lora_A._fast_lora, X.ravel(), out = temp_lora)
            out.addmv_(lora_B._fast_lora, temp_lora, alpha = lora_S)
        else:
            out = out.view(bsz, out_dim)
            temp_lora = torch_mm(
                X.view(bsz, in_dim), lora_A._fast_lora.t(), out = temp_lora
            )
            out.addmm_(temp_lora, lora_B._fast_lora.t(), alpha = lora_S)
        out = out.view(bsz, 1, out_dim)

    if bias is not None:
        out += bias

    return out
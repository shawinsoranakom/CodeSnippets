def calculate_diff(batch_size, seq_len, hidden_size, use_residual=True):
    dtype = torch.bfloat16
    x = torch.randn(batch_size, seq_len, hidden_size, dtype=dtype, device="cuda")
    weight = torch.ones(hidden_size, dtype=dtype, device="cuda")
    residual = torch.randn_like(x) if use_residual else None

    output_naive = rmsnorm_naive(
        x.clone(), weight, residual.clone() if residual is not None else None
    )
    output_flashinfer = rmsnorm_flashinfer(
        x.clone(), weight, residual.clone() if residual is not None else None
    )
    output_vllm = rmsnorm_vllm(
        x.clone(), weight, residual.clone() if residual is not None else None
    )

    if use_residual:
        output_naive = output_naive[0]
        output_flashinfer = output_flashinfer[0]
        output_vllm = output_vllm[0]

    print(f"Naive output={output_naive}")
    print(f"FlashInfer output={output_flashinfer}")
    print(f"vLLM output={output_vllm}")

    if torch.allclose(
        output_naive, output_flashinfer, atol=1e-2, rtol=1e-2
    ) and torch.allclose(output_naive, output_vllm, atol=1e-2, rtol=1e-2):
        print("✅ All implementations match")
    else:
        print("❌ Implementations differ")
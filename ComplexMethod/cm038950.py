def benchmark_shape(
    m: int,
    n: int,
    k: int,
    warmup: int = 100,
    repeat: int = 10000,
    verbose: bool = False,
) -> dict:
    """Benchmark all implementations for a specific (m, n, k) shape."""
    if verbose:
        print(f"\n=== Benchmarking shape: m={m}, n={n}, k={k} ===")

    # Create test tensors
    A = torch.randn((m, k), device="cuda", dtype=torch.bfloat16)
    B = torch.randn((n, k), device="cuda", dtype=torch.bfloat16)

    # Reference result in BF16
    torch.accelerator.synchronize()
    C_ref = A @ B.t()

    # Pre-quantize B for all implementations
    # (weights can be pre-quantized offline)
    B_deepgemm, B_scale_deepgemm = per_block_cast_to_fp8(B, [128, 128], use_ue8m0=True)
    B_vllm, B_scale_vllm = per_block_cast_to_fp8(B, [128, 128], use_ue8m0=True)

    # Block size configuration
    block_size = [128, 128]

    # Pre-quantize A for all implementations
    A_deepgemm, A_scale_deepgemm = per_token_group_quant_fp8(
        A, block_size[1], column_major_scales=True, tma_aligned_scales=True
    )
    C_deepgemm = torch.empty((m, n), device="cuda", dtype=torch.bfloat16)
    A_vllm, A_scale_vllm = per_token_group_quant_fp8(A, block_size[1])
    A_vllm_cutlass, A_scale_vllm_cutlass = per_token_group_quant_fp8(
        A, block_size[1], column_major_scales=True
    )

    # === DeepGEMM Implementation ===
    def deepgemm_gemm():
        fp8_gemm_nt(
            (A_deepgemm, A_scale_deepgemm), (B_deepgemm, B_scale_deepgemm), C_deepgemm
        )
        return C_deepgemm

    # === vLLM Triton Implementation ===
    def vllm_triton_gemm():
        return w8a8_triton_block_scaled_mm(
            A_vllm,
            B_vllm,
            A_scale_vllm,
            B_scale_vllm,
            block_size,
            output_dtype=torch.bfloat16,
        )

    # === vLLM CUTLASS Implementation ===
    def vllm_cutlass_gemm():
        return ops.cutlass_scaled_mm(
            A_vllm_cutlass,
            B_vllm.T,
            scale_a=A_scale_vllm_cutlass,
            scale_b=B_scale_vllm.T,
            out_dtype=torch.bfloat16,
        )

    # Run correctness check first
    if verbose:
        print("Running correctness check...")
    C_deepgemm = deepgemm_gemm()
    C_vllm_triton = vllm_triton_gemm()
    C_vllm_cutlass = vllm_cutlass_gemm()

    deepgemm_diff = calc_diff(C_deepgemm, C_ref)
    vllm_triton_diff = calc_diff(C_vllm_triton, C_ref)
    vllm_cutlass_diff = calc_diff(C_vllm_cutlass, C_ref)

    if verbose:
        print(f"DeepGEMM vs Reference difference: {deepgemm_diff:.6f}")
        print(f"vLLM Triton vs Reference difference: {vllm_triton_diff:.6f}")
        print(f"vLLM CUTLASS vs Reference difference: {vllm_cutlass_diff:.6f}")
        print(
            "vLLM Triton vs DeepGEMM difference: "
            f"{calc_diff(C_vllm_triton, C_deepgemm):.6f}"
        )
        print(
            "vLLM CUTLASS vs DeepGEMM difference: "
            f"{calc_diff(C_vllm_cutlass, C_deepgemm):.6f}"
        )

    # Benchmark implementations
    implementations = {
        "DeepGEMM": deepgemm_gemm,
        "vLLM Triton": vllm_triton_gemm,
        "vLLM CUTLASS": vllm_cutlass_gemm,
    }

    benchmark_results = {"shape": {"m": m, "n": n, "k": k}, "implementations": {}}

    for name, func in implementations.items():
        # Warmup
        for _ in range(warmup):
            func()
            torch.accelerator.synchronize()

        # Timing loop
        torch.accelerator.synchronize()
        start = time.time()
        for _ in range(repeat):
            func()
        torch.accelerator.synchronize()
        end = time.time()

        # Calculate timing and TFLOPS
        avg_time_ms = (end - start) / repeat * 1000
        avg_time_us = avg_time_ms * 1000
        tflops = 2 * m * n * k / (avg_time_ms * 1e-3) / 1e12
        gb_s = (m * k + k * n + m * n * 2) / 1e9 / (avg_time_ms * 1e-3)

        benchmark_results["implementations"][name] = {
            "time_ms": avg_time_ms,
            "time_us": avg_time_us,
            "tflops": tflops,
            "gb_s": gb_s,
            "diff": {
                "DeepGEMM": 0.0
                if name == "DeepGEMM"
                else calc_diff(func(), C_deepgemm),
                "Reference": deepgemm_diff
                if name == "DeepGEMM"
                else (vllm_triton_diff if name == "vLLM Triton" else vllm_cutlass_diff),
            },
        }

        if verbose:
            print(f"{name}: {avg_time_ms:.3f} ms, {tflops:.2f} TFLOPS, {gb_s:.2f} GB/s")

    # Calculate speedups
    baseline = benchmark_results["implementations"]["DeepGEMM"]["time_ms"]
    for name, data in benchmark_results["implementations"].items():
        if name != "DeepGEMM":
            speedup = baseline / data["time_ms"]
            benchmark_results["implementations"][name]["speedup_vs_deepgemm"] = speedup
            if verbose:
                print(
                    f"DeepGEMM is {1 / speedup:.2f}x "
                    f"{'faster' if 1 / speedup > 1 else 'slower'} than {name}"
                )

    vllm_triton_time = benchmark_results["implementations"]["vLLM Triton"]["time_ms"]
    vllm_cutlass_time = benchmark_results["implementations"]["vLLM CUTLASS"]["time_ms"]
    cutlass_vs_triton = vllm_triton_time / vllm_cutlass_time
    benchmark_results["implementations"]["vLLM CUTLASS"]["speedup_vs_triton"] = (
        cutlass_vs_triton
    )
    if verbose:
        print(
            f"vLLM CUTLASS is {cutlass_vs_triton:.2f}x "
            f"{'faster' if cutlass_vs_triton > 1 else 'slower'} than vLLM Triton"
        )

    return benchmark_results
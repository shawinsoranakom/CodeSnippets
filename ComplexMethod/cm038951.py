def run_benchmarks(verbose: bool = False):
    """Run benchmarks for a set of common shapes."""
    print("===== STARTING FP8 GEMM BENCHMARK =====")

    # Make sure we're using the GPU
    if not torch.cuda.is_available():
        print("CUDA not available! Tests require GPU.")
        return

    # Print system information
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Triton version: {triton.__version__}")
    print(f"Using device: {torch.cuda.get_device_name()}")

    # Enable TF32 for better performance
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    # Set seeds for reproducibility
    set_random_seed(42)
    # Define benchmark shapes (m, n, k)
    shapes = [
        (8, 4096, 7168),
        (8, 7168, 18432),
        (8, 18432, 7168),
        (64, 4096, 7168),
        (64, 7168, 18432),
        (64, 18432, 7168),
        (64, 24576, 1536),
        (64, 32768, 512),
        (64, 7168, 16384),
        (128, 4096, 7168),
        (128, 7168, 18432),
        (128, 18432, 7168),
        (1024, 4096, 7168),
        (1024, 18432, 7168),
        (2048, 4096, 7168),
        (4096, 4096, 7168),
    ]
    shapes = [
        # (64, 2112, 7168),
        (64, 24576, 1536),
        (64, 32768, 512),
        (64, 7168, 16384),
        (64, 4096, 7168),
        (64, 7168, 2048),
        # (128, 2112, 7168),
        (128, 24576, 1536),
        (128, 32768, 512),
        (128, 7168, 16384),
        (128, 4096, 7168),
        (128, 7168, 2048),
        # (4096, 2112, 7168),
        (4096, 24576, 1536),
        (4096, 32768, 512),
        (4096, 7168, 16384),
        (4096, 4096, 7168),
        (4096, 7168, 2048),
    ]

    all_results = []
    for m, n, k in shapes:
        result = benchmark_shape(m, n, k, verbose=verbose)
        all_results.append(result)

    # Print results in a nicely formatted table
    print("\n===== PERFORMANCE COMPARISON =====")

    # Print DeepGEMM table
    deepgemm_headers = ["m", "n", "k", "Time (μs)", "TFLOPS", "GB/s"]
    deepgemm_rows = []
    for result in all_results:
        shape = result["shape"]
        impl_data = result["implementations"]["DeepGEMM"]
        deepgemm_rows.append(
            [
                shape["m"],
                shape["n"],
                shape["k"],
                f"{impl_data['time_us']:.1f}",
                f"{impl_data['tflops']:.1f}",
                f"{impl_data['gb_s']:.1f}",
            ]
        )

    print_table(deepgemm_headers, deepgemm_rows, title="DeepGEMM Implementation:")

    # Print vLLM Triton table
    triton_headers = ["m", "n", "k", "Time (μs)", "TFLOPS", "GB/s", "vs DeepGEMM"]
    triton_rows = []
    for result in all_results:
        shape = result["shape"]
        impl_data = result["implementations"]["vLLM Triton"]
        speedup = impl_data.get("speedup_vs_deepgemm", 1.0)
        triton_rows.append(
            [
                shape["m"],
                shape["n"],
                shape["k"],
                f"{impl_data['time_us']:.1f}",
                f"{impl_data['tflops']:.1f}",
                f"{impl_data['gb_s']:.1f}",
                format_speedup(speedup),
            ]
        )

    print_table(triton_headers, triton_rows, title="vLLM Triton Implementation:")

    # Print vLLM CUTLASS table
    cutlass_headers = [
        "m",
        "n",
        "k",
        "Time (μs)",
        "TFLOPS",
        "GB/s",
        "vs DeepGEMM",
        "vs Triton",
    ]
    cutlass_rows = []
    for result in all_results:
        shape = result["shape"]
        impl_data = result["implementations"]["vLLM CUTLASS"]
        vs_deepgemm = impl_data.get("speedup_vs_deepgemm", 1.0)
        vs_triton = impl_data.get("speedup_vs_triton", 1.0)
        cutlass_rows.append(
            [
                shape["m"],
                shape["n"],
                shape["k"],
                f"{impl_data['time_us']:.1f}",
                f"{impl_data['tflops']:.1f}",
                f"{impl_data['gb_s']:.1f}",
                format_speedup(vs_deepgemm),
                format_speedup(vs_triton),
            ]
        )

    print_table(cutlass_headers, cutlass_rows, title="vLLM CUTLASS Implementation:")

    # Calculate and print averages
    print("\n===== AVERAGE PERFORMANCE =====")

    implementations = ["DeepGEMM", "vLLM Triton", "vLLM CUTLASS"]
    avg_metrics = {
        impl: {"tflops": 0, "gb_s": 0, "time_ms": 0} for impl in implementations
    }

    for result in all_results:
        for impl in implementations:
            impl_data = result["implementations"][impl]
            avg_metrics[impl]["tflops"] += impl_data["tflops"]
            avg_metrics[impl]["gb_s"] += impl_data["gb_s"]
            avg_metrics[impl]["time_ms"] += impl_data["time_ms"]

    num_shapes = len(all_results)
    avg_headers = ["Implementation", "Avg TFLOPS", "Avg GB/s", "Avg Time (ms)"]
    avg_rows = []

    for impl in implementations:
        avg_tflops = avg_metrics[impl]["tflops"] / num_shapes
        avg_mem_bw = avg_metrics[impl]["gb_s"] / num_shapes
        avg_time = avg_metrics[impl]["time_ms"] / num_shapes
        avg_rows.append(
            [impl, f"{avg_tflops:.2f}", f"{avg_mem_bw:.2f}", f"{avg_time:.2f}"]
        )

    print_table(avg_headers, avg_rows)

    # Calculate average speedups
    avg_speedups = {
        "DeepGEMM vs vLLM Triton": 0,
        "DeepGEMM vs vLLM CUTLASS": 0,
        "vLLM CUTLASS vs vLLM Triton": 0,
    }

    for result in all_results:
        deepgemm_time = result["implementations"]["DeepGEMM"]["time_ms"]
        vllm_triton_time = result["implementations"]["vLLM Triton"]["time_ms"]
        vllm_cutlass_time = result["implementations"]["vLLM CUTLASS"]["time_ms"]

        avg_speedups["DeepGEMM vs vLLM Triton"] += vllm_triton_time / deepgemm_time
        avg_speedups["DeepGEMM vs vLLM CUTLASS"] += vllm_cutlass_time / deepgemm_time
        avg_speedups["vLLM CUTLASS vs vLLM Triton"] += (
            vllm_triton_time / vllm_cutlass_time
        )

    print("\n===== AVERAGE SPEEDUPS =====")
    speedup_headers = ["Comparison", "Speedup"]
    speedup_rows = []
    for comparison, total in avg_speedups.items():
        avg_speedup = total / num_shapes
        status = "faster" if avg_speedup > 1 else "slower"
        speedup_rows.append([comparison, f"{avg_speedup:.2f}x {status}"])

    print_table(speedup_headers, speedup_rows)

    # Average accuracy comparison
    print("\n===== ACCURACY COMPARISON =====")
    avg_diff = {impl: 0 for impl in implementations}

    for result in all_results:
        for impl in implementations:
            avg_diff[impl] += result["implementations"][impl]["diff"]["Reference"]

    diff_headers = ["Implementation", "Avg Diff vs Reference"]
    diff_rows = []
    for impl in implementations:
        diff_rows.append([impl, f"{avg_diff[impl] / num_shapes:.6f}"])

    print_table(diff_headers, diff_rows)
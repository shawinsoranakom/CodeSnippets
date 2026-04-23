def test_merge_attn_states(
    prefill_tokens_with_context: int | None,
    num_tokens: int,
    num_query_heads: int,
    head_size: int,
    input_dtype: torch.dtype,
    use_fp8: bool,
):
    if not current_platform.is_cuda():
        pytest.skip(
            "Currently only support compare triton merge_attn_states "
            "with custom cuda merge_attn_states kernel"
        )

    NUM_TOKENS = num_tokens
    NUM_HEADS = num_query_heads
    HEAD_SIZE = head_size

    # When use_fp8 is set, inputs stay as input_dtype (bf16/fp16/fp32)
    # and output becomes FP8.
    output_dtype = input_dtype
    output_scale = None
    if use_fp8:
        output_dtype = current_platform.fp8_dtype()
        output_scale = torch.tensor([0.05], dtype=torch.float32, device="cuda")

    print(
        f"\nNUM_TOKENS:{NUM_TOKENS}, NUM_HEADS:{NUM_HEADS}, "
        f"HEAD_SIZE:{HEAD_SIZE}, input_dtype: {input_dtype}, "
        f"output_dtype: {output_dtype}, use_fp8: {use_fp8}, "
        f"prefill_tokens_with_context: {prefill_tokens_with_context}, "
        f"Device: {current_platform.get_device_name()}"
    )

    # prefix_lse and suffix_lse contain inf and normal values
    prefix_lse = torch.randn(NUM_HEADS, NUM_TOKENS, dtype=torch.float32, device="cuda")
    suffix_lse = torch.randn(NUM_HEADS, NUM_TOKENS, dtype=torch.float32, device="cuda")

    # Generate boolean masks
    mask_prefix = torch.rand(NUM_HEADS, NUM_TOKENS) < 0.1
    mask_suffix = torch.rand(NUM_HEADS, NUM_TOKENS) < 0.1
    # Ensure that the same position is not True at the same time
    combined_mask = torch.logical_and(mask_prefix, mask_suffix)
    mask_prefix = torch.logical_and(mask_prefix, ~combined_mask)
    mask_suffix = torch.logical_and(mask_suffix, ~combined_mask)

    prefix_lse[mask_prefix] = float("inf")
    suffix_lse[mask_suffix] = float("inf")

    # Other input tensors (need to be initialized but
    # no actual calculation needed)
    output = torch.zeros(
        (NUM_TOKENS, NUM_HEADS, HEAD_SIZE), dtype=output_dtype, device="cuda"
    )
    output_lse = torch.zeros(
        (NUM_HEADS, NUM_TOKENS), dtype=torch.float32, device="cuda"
    )
    prefix_output = torch.randn(
        (NUM_TOKENS, NUM_HEADS, HEAD_SIZE), dtype=input_dtype, device="cuda"
    )
    suffix_output = torch.randn(
        (NUM_TOKENS, NUM_HEADS, HEAD_SIZE), dtype=input_dtype, device="cuda"
    )

    warmup_times = 2
    repeat_times = 20

    output_torch = output.clone()
    output_lse_torch = output_lse.clone()
    total_time_torch_kernel = 0
    start = torch.Event(enable_timing=True)
    end = torch.Event(enable_timing=True)

    # 0. Run the Torch kernel
    prefix_lse_torch = prefix_lse.clone()
    suffix_lse_torch = suffix_lse.clone()
    for _ in range(warmup_times):
        output_torch, output_lse_torch = merge_attn_states_torch(
            output_torch,
            prefix_output,
            prefix_lse_torch,
            suffix_output,
            suffix_lse_torch,
            output_lse_torch,
            prefill_tokens_with_context,
            output_scale,
        )
    torch.accelerator.synchronize()

    for _ in range(repeat_times):
        start.record()
        output_torch, output_lse_torch = merge_attn_states_torch(
            output_torch,
            prefix_output,
            prefix_lse_torch,
            suffix_output,
            suffix_lse_torch,
            output_lse_torch,
            prefill_tokens_with_context,
            output_scale,
        )
        end.record()
        torch.accelerator.synchronize()
        total_time_torch_kernel += start.elapsed_time(end)

    avg_time_torch_kernel = total_time_torch_kernel / repeat_times

    # 1. Run the Triton kernel
    output_ref_triton = output.clone()
    output_lse_ref_triton = output_lse.clone()

    total_time_triton_kernel = 0
    start = torch.Event(enable_timing=True)
    end = torch.Event(enable_timing=True)

    for _ in range(warmup_times):
        merge_attn_states_triton(
            output_ref_triton,
            prefix_output,
            prefix_lse,
            suffix_output,
            suffix_lse,
            output_lse_ref_triton,
            prefill_tokens_with_context,
            output_scale,
        )
    torch.accelerator.synchronize()

    for _ in range(repeat_times):
        start.record()
        merge_attn_states_triton(
            output_ref_triton,
            prefix_output,
            prefix_lse,
            suffix_output,
            suffix_lse,
            output_lse_ref_triton,
            prefill_tokens_with_context,
            output_scale,
        )
        end.record()
        torch.accelerator.synchronize()
        total_time_triton_kernel += start.elapsed_time(end)

    avg_time_triton_kernel = total_time_triton_kernel / repeat_times

    # 2. Run the CUDA kernel
    total_time_cuda_kernel = 0
    output_cuda = output.clone()
    output_lse_cuda = output_lse.clone()

    for _ in range(warmup_times):
        merge_attn_states_cuda(
            output_cuda,
            prefix_output,
            prefix_lse,
            suffix_output,
            suffix_lse,
            output_lse_cuda,
            prefill_tokens_with_context,
            output_scale,
        )
    torch.accelerator.synchronize()

    for _ in range(repeat_times):
        start.record()
        merge_attn_states_cuda(
            output_cuda,
            prefix_output,
            prefix_lse,
            suffix_output,
            suffix_lse,
            output_lse_cuda,
            prefill_tokens_with_context,
            output_scale,
        )
        end.record()
        torch.accelerator.synchronize()
        total_time_cuda_kernel += start.elapsed_time(end)

    avg_time_cuda_kernel = total_time_cuda_kernel / repeat_times

    # 3. Performance compare
    performance_improved = avg_time_triton_kernel / avg_time_cuda_kernel
    print(f" Torch time: {avg_time_torch_kernel:.6f}ms")
    print(f"Triton time: {avg_time_triton_kernel:.6f}ms")
    print(
        f"  CUDA time: {avg_time_cuda_kernel:.6f}ms, "
        f"Performance: {performance_improved:.5f}x"
    )
    print("-" * 100)

    # 4. Correctness compare
    # Liger Kernel: Efficient Triton Kernels for LLM Training
    # https://arxiv.org/pdf/2410.10989, 3.3 Correctness
    # use rtol = 1e-2 for bfloat16.
    if use_fp8:
        # Compare in dequantized space (multiply back by scale) so that
        # absolute differences reflect real precision, not amplified FP8
        # quantization steps.
        atol, rtol = 1e-1, 1e-1
        assert output_scale is not None
        scale = output_scale.item()
    elif output_dtype == torch.bfloat16:
        atol, rtol = 1e-3, 1e-2
        scale = 1.0
    else:
        atol, rtol = 1e-3, 1e-3
        scale = 1.0

    def diff(a: torch.Tensor, b: torch.Tensor):
        max_diff = torch.max(torch.abs(a.float() - b.float()))
        return max_diff

    # Use Triton output as reference because we want to replace
    # the Triton kernel with custom CUDA kernel for merge attn
    # states operation.
    output_ref = output_ref_triton
    output_lse_ref = output_lse_ref_triton
    torch.testing.assert_close(
        output_cuda.float() * scale,
        output_ref.float() * scale,
        atol=atol,
        rtol=rtol,
    )
    print(
        "Output all match, max abs diff (dequantized):"
        if use_fp8
        else "Output all match, max abs diff:"
    )
    _diff = diff(output_ref.float() * scale, output_torch.float() * scale)
    print(f"(Triton vs Torch) : {_diff}")
    _diff = diff(output_torch.float() * scale, output_cuda.float() * scale)
    print(f"  (CUDA vs Torch) : {_diff}")
    _diff = diff(output_ref.float() * scale, output_cuda.float() * scale)
    print(f"  (CUDA vs Triton): {_diff}")
    print("-" * 100)

    torch.testing.assert_close(
        output_lse_cuda.float(), output_lse_ref.float(), atol=atol, rtol=rtol
    )
    print("Output LSE all match, max abs diff:")
    print(f"(Triton vs Torch) : {diff(output_lse_torch, output_lse_ref)}")
    print(f"  (CUDA vs Torch) : {diff(output_lse_torch, output_lse_cuda)}")
    print(f"  (CUDA vs Triton): {diff(output_lse_ref, output_lse_cuda)}")
    print("-" * 100)

    print(
        "All output values test passed! All inf values "
        "are correctly replaced with -inf."
    )
    print("-" * 100)

    device = current_platform.get_device_name()
    all_case_info.append(
        (
            NUM_TOKENS,
            NUM_HEADS,
            HEAD_SIZE,
            output_dtype,
            device,
            avg_time_torch_kernel,
            avg_time_triton_kernel,
            avg_time_cuda_kernel,
            performance_improved,
        )
    )
    if len(all_case_info) == (
        len(NUM_BATCH_TOKENS) * len(HEAD_SIZES) * len(NUM_QUERY_HEADS) * len(DTYPES)
    ):
        generate_markdown_table()
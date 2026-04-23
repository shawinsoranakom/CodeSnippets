def _add_nv_gemm_choices_impl(
    choices: list[ChoiceCaller],
    layout: Layout,
    input_nodes: list[Buffer],
    variant: GemmVariant,
    accumulator_type: torch.dtype,
    mm_inputs: MMKernelInputs | None = None,
    scale_type_a: Any | None = None,
    scale_type_b: Any | None = None,
    swizzle_type_a: Any | None = None,
    swizzle_type_b: Any | None = None,
) -> None:
    """
    Unified implementation for adding NVIDIA Universal GEMM choices.

    Args:
        choices: List to append ChoiceCaller objects to
        layout: Output layout
        input_nodes: Input tensor nodes
        variant: The GEMM variant (determines behavior)
        accumulator_type: Accumulator dtype
        mm_inputs: Optional MMKernelInputs for heuristics
        scale_type_a: ScalingType for A (required for SCALED_GEMM)
        scale_type_b: ScalingType for B (required for SCALED_GEMM)
        swizzle_type_a: SwizzleType for A (required for SCALED_GEMM)
        swizzle_type_b: SwizzleType for B (required for SCALED_GEMM)
    """
    import cutlass_api

    from torch._inductor.codegen.nv_universal_gemm.kernel_cache import (
        get_compatible_kernels,
    )

    # Create dummy tensors for cutlass_api's supports() checks
    dummy_tensors = [
        _create_dummy_tensor_from_layout(node.get_layout()) for node in input_nodes
    ]
    out_tensor = _create_dummy_tensor_from_layout(layout)

    if any(t is None for t in dummy_tensors) or out_tensor is None:
        log.debug("Failed to create dummy tensors for %s", variant.op_name)
        return

    if variant == GemmVariant.GROUPED_GEMM:
        a_tensor, b_tensor, offs_tensor = dummy_tensors
        assert b_tensor is not None
        args = cutlass_api.arguments.GroupedGemmArguments(
            a_tensor,
            b_tensor,
            out_tensor,
            accumulator_type=accumulator_type,
            offsets=offs_tensor,
        )
    elif variant == GemmVariant.SCALED_GEMM:
        from cutlass_api.arguments import ScaledTensor

        scale_mode_a, swizzle_mode_a = to_cutlass_scale_mode(
            scale_type_a, swizzle_type_a
        )
        scale_mode_b, swizzle_mode_b = to_cutlass_scale_mode(
            scale_type_b, swizzle_type_b
        )
        if scale_mode_a is None or scale_mode_b is None:
            return

        a_tensor, b_tensor, scale_a_tensor, scale_b_tensor = dummy_tensors
        scaled_a = ScaledTensor(
            a_tensor,
            scale_a_tensor,
            scale_mode_a,
            swizzle_mode_a,
        )
        scaled_b = ScaledTensor(
            b_tensor,
            scale_b_tensor,
            scale_mode_b,
            swizzle_mode_b,
        )
        args = cutlass_api.arguments.GemmArguments(
            scaled_a,
            scaled_b,
            out_tensor,
            accumulator_type=accumulator_type,
        )
    else:
        a_tensor, b_tensor = dummy_tensors
        args = cutlass_api.arguments.GemmArguments(
            a_tensor,
            b_tensor,
            out_tensor,
            accumulator_type=accumulator_type,
        )

    cc = get_cuda_arch()
    if cc is None:
        log.debug("Failed to get CUDA arch")
        return
    cc_int = int(cc)

    kernels = get_compatible_kernels(args, cc_int, metadata_filter=_exclude_efc_kernels)
    if not kernels:
        log.debug("No compatible %s kernels found", variant.op_name)
        return

    max_configs = config.nvgemm_max_profiling_configs or len(kernels)
    if variant in (GemmVariant.GEMM, GemmVariant.SCALED_GEMM) and mm_inputs is not None:
        heuristics = get_nvgemm_heuristics()
        kernels = heuristics.filter_kernels(
            kernels, mm_inputs, max_configs, accumulator_type
        )
    else:
        # TODO(nikhilap): Enable heuristics for grouped GEMM
        # when nvMatmulHeuristics adds support
        kernels = kernels[:max_configs]

    # Add callers for each kernel
    num_added = 0
    for kernel in kernels:
        name = f"{variant.op_name}_{next(NVUniversalGemmCaller.index_counter)}"
        workspace_size = kernel.get_workspace_size(args)
        try:
            caller = NVUniversalGemmCaller(
                name=name,
                input_nodes=input_nodes,
                layout=layout,
                kernel=kernel,
                accumulator_type=accumulator_type,
                workspace_size=workspace_size,
                variant=variant,
                scale_type_a=scale_type_a,
                scale_type_b=scale_type_b,
                swizzle_type_a=swizzle_type_a,
                swizzle_type_b=swizzle_type_b,
            )
            choices.append(caller)
            num_added += 1
        except Exception:
            log.debug("Failed to create %s choice", variant.op_name, exc_info=True)

    log.debug("Added %d %s choices", num_added, variant.op_name)
def tuned_scaled_mm(
    mat_a,
    mat_b,
    scale_a,
    scale_b,
    bias=None,
    scale_result=None,
    out_dtype=None,
    use_fast_accum=False,
    layout=None,
):
    """
    Performs an optimized matrix multiplication where scaling factors are applied
    to the inputs and/or output.

    Args:
        mat1 (Tensor): First input matrix
        mat2 (Tensor): Second input matrix
        scale1 (Tensor): Scale factor applied to mat1 (supports broadcasting)
        scale2 (Tensor): Scale factor applied to mat2 (supports broadcasting)
        bias (Tensor, optional): Optional bias tensor to add to the result
        layout: Layout hint for optimization

    Returns:
        Tensor: The result of the scaled matrix multiplication
    """
    # TODO(coconutruben): integrate into MMKernelInputs when all callsites use that
    m, n, k, layout, mat_a, mat_b = mm_args(
        mat_a, mat_b, layout=layout, out_dtype=out_dtype
    )
    # below is for getting an overview logging info of inductor mms
    counters["aten_mm_info"][f"aten._scaled_mm.default_{m}_{n}_{k}"] += 1
    log.info(
        "Tuned aten._scaled_mm.default: m=%s, n=%s, k=%s, mat1_dtype=%s, mat2_dtype=%s, output_layout=%s",
        m,
        n,
        k,
        mat_a.get_dtype(),
        mat_b.get_dtype(),
        layout,
    )
    name = "scaled_mm"
    check_supported_striding(mat_a, mat_b)

    scale_a_real, scale_b_real = realize_inputs(scale_a, scale_b)

    input_nodes: list[Any]

    if not bias:
        input_nodes = [mat_a, mat_b, scale_a_real, scale_b_real]
    else:
        bias_real = realize_inputs(bias)
        input_nodes = [mat_a, mat_b, scale_a_real, scale_b_real, bias_real]

    # Create MMKernelInputs for Scaled MM (matrices are at indices 0, 1)
    kernel_inputs = MMKernelInputs(
        input_nodes, mat1_idx=0, mat2_idx=1, out_dtype=out_dtype
    )

    choices: list[ChoiceCaller] = []

    # Collect all templates for unified call
    templates_to_use: list[ExternKernelChoice | KernelTemplate] = []
    kwarg_overrides = {}

    if use_aten_gemm_kernels():
        templates_to_use.append(aten__fp8_mm)
        kwarg_overrides[aten__fp8_mm.uid] = dict(
            out_dtype=out_dtype, use_fast_accum=use_fast_accum
        )

    _, is_nonzero = _is_static_problem(layout)

    if (
        # We dont have triton lowerings for the MX variants yet
        scale_a.dtype == torch.float32
        and is_nonzero
        and use_triton_template(layout, enable_float8=True, check_max_autotune=False)
    ):
        overriders = dict(USE_FAST_ACCUM=use_fast_accum)

        scale_a_size, scale_b_size = scale_a_real.shape, scale_b_real.shape

        scale_option_a, scale_option_b = get_scaling_options(
            mat_a, mat_b, scale_a_size, scale_b_size
        )

        # TODO (paulzhan): There is no template that exists for bias and TMA
        # Don't run tma template currently if bias exist
        if (
            use_triton_tma_template(mat_a, mat_b, output_layout=layout, add_guards=True)
            and not bias
        ):
            overriders["SCALE_RECIPE_A"] = scale_option_a.value
            overriders["SCALE_RECIPE_B"] = scale_option_b.value

            if use_triton_scaling_template(
                scale_option_a, scale_option_b, epilogue_scaling_types
            ):
                templates_to_use.append(scaled_mm_device_tma_epilogue_scaling_template)
                kwarg_overrides[scaled_mm_device_tma_epilogue_scaling_template.uid] = (
                    overriders
                )
            elif use_triton_scaling_template(
                scale_option_a, scale_option_b, main_loop_scaling_types
            ):
                overriders["TILE_SIZE_A"] = get_tile_size(scale_option_a)
                overriders["TILE_SIZE_B"] = get_tile_size(scale_option_b)

                templates_to_use.append(scaled_mm_device_tma_main_loop_scaling_template)
                kwarg_overrides[scaled_mm_device_tma_main_loop_scaling_template.uid] = (
                    overriders
                )
            else:
                raise AssertionError(
                    "Inductor Triton does not support scaling options that are present "
                    + "in both epilogue scaling and main loop scaling"
                )

        if (
            use_triton_blackwell_tma_template(
                mat_a, mat_b, output_layout=layout, add_guards=True
            )
            and not bias
        ):
            templates_to_use.append(blackwell_ws_persistent_device_tma_mm_template)
            kwarg_overrides[blackwell_ws_persistent_device_tma_mm_template.uid] = (
                overriders
            )

        if use_triton_scaling_template(
            scale_option_a, scale_option_b, epilogue_scaling_types
        ):
            templates_to_use.append(mm_template)
            kwarg_overrides[mm_template.uid] = overriders

    # Single unified call for all templates
    choices.extend(
        V.choices.get_template_configs(
            kernel_inputs,
            templates_to_use,
            name,
            kwarg_overrides=kwarg_overrides,
        )
    )

    # NVGEMM get_kernels() will return empty if the scaling mode/dtype is unsupported
    if is_nonzero and use_nv_universal_gemm_template(layout, m, n, k, mat_a, mat_b):
        from ..codegen.nv_universal_gemm import add_nv_universal_scaled_gemm_choices

        add_nv_universal_scaled_gemm_choices(
            choices,
            layout,
            input_nodes,
            kernel_inputs=kernel_inputs,
        )

    # Early return for MX variants
    if scale_a.dtype != torch.float32:
        node, _ = autotune_select_algorithm(name, choices, input_nodes, layout)
        return node

    if (
        is_nonzero
        and use_cutlass_template(layout, m, n, k)
        and _use_cutlass_for_op(name)
    ):
        CUTLASS3xGemmTemplate.add_cutlass_gemm_choices(
            choices,
            layout,
            kernel_inputs.nodes(),  # type: ignore[arg-type]
            use_fast_accum=use_fast_accum,  # type: ignore[arg-type]
        )

    if is_nonzero and use_ck_gemm_template(layout, m, n, k):
        CKGemmTemplate.add_ck_gemm_choices(choices, layout, kernel_inputs.nodes())

    node, _ = autotune_select_algorithm(name, choices, kernel_inputs.nodes(), layout)
    return node
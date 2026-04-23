def tuned_addmm(inp, mat1, mat2, *, alpha=1, beta=1, layout=None):
    """
    Lowering for autotuning aten.addmm with different backends (Aten, Triton, CUTLASS, etc.)
    """
    if use_native_matmul(mat1, mat2):
        if beta == 0:
            arg1 = 0
        else:
            arg1 = lowerings[aten.mul](beta, inp)

        if alpha == 0:
            arg2 = 0
        else:
            arg2 = lowerings[aten.mul](alpha, lowerings[aten.mm](mat1, mat2))

        return lowerings[aten.add](arg1, arg2)

    # TODO(coconutruben): integrate into MMKernelInputs when all callsites use that
    m, n, k, layout, mat1, mat2, inp_expanded = mm_args(mat1, mat2, inp, layout=layout)
    static_shape, is_nonzero = _is_static_problem(layout)
    name = "addmm"

    # Create MMKernelInputs for AddMM at the top
    kernel_inputs = MMKernelInputs(
        [inp_expanded, mat1, mat2], scalars=dict(alpha=alpha, beta=beta)
    )
    kernel_inputs_aten = MMKernelInputs(
        [inp, mat1, mat2], scalars=dict(alpha=alpha, beta=beta)
    )

    choices: list[ChoiceCaller] = []

    # below is for getting an overview logging info of inductor mms
    counters["aten_mm_info"][f"aten.addmm_{m}_{n}_{k}"] += 1
    log.info(
        "Tuned aten.addmm: m=%s, n=%s, k=%s, mat1_dtype=%s, mat2_dtype=%s, output_layout=%s",
        m,
        n,
        k,
        mat1.get_dtype(),
        mat2.get_dtype(),
        layout,
    )
    if (not is_nonzero) or (
        not (inductor_config.max_autotune or inductor_config.max_autotune_gemm)
    ):
        choices.extend(
            V.choices.get_template_configs(
                kernel_inputs_aten,
                [aten_addmm],
                name,
            )
        )
        node, _ = autotune_select_algorithm(
            name, choices, kernel_inputs.nodes(), layout
        )
        return node

    templates_to_use: list[ExternKernelChoice | KernelTemplate] = []

    if use_aten_gemm_kernels():
        aten_templates: list[ExternKernelChoice | KernelTemplate] = [aten_addmm]
        if (
            inp.get_stride()[0] == 0
            and len(inp.get_size()) == 2
            and inductor_config.triton.autotune_cublasLt
            and not V.graph.cpp_wrapper  # bias_addmm only has a Python implementation
        ):
            aten_templates.append(aten_bias_addmm)

        # On ROCm, ATen choices use original bias input; non-ROCm keeps unified inputs.
        choices.extend(
            V.choices.get_template_configs(kernel_inputs_aten, aten_templates, name)
        )

    if is_nonzero and use_triton_template(layout, check_max_autotune=False):
        templates_to_use.append(mm_template)

        if use_triton_blackwell_tma_template(
            mat1, mat2, output_layout=layout, add_guards=True
        ):
            templates_to_use.append(blackwell_ws_persistent_device_tma_mm_template)
        elif use_triton_tma_template(mat1, mat2, output_layout=layout, add_guards=True):
            if torch.version.hip is None:
                templates_to_use.append(persistent_tma_mm_template)
            else:
                templates_to_use.append(persistent_mm_template)

        templates_to_use.append(addmm_contiguous_subgraph_template)

    # Single unified call for all templates
    choices.extend(
        V.choices.get_template_configs(kernel_inputs, templates_to_use, name)
    )

    if (
        is_nonzero
        and use_cutlass_template(layout, m, n, k)
        and _use_cutlass_for_op(name)
    ):
        CUTLASS3xGemmTemplate.add_cutlass_gemm_choices(
            choices,
            layout,
            # reorder here because CUTLASS expects (x, w, bias) but torch
            # is bias, x, w
            kernel_inputs.nodes(reorder=[1, 2, 0]),
            alpha=alpha,
            beta=beta,
            input_reorder=[2, 0, 1],
        )

    if is_nonzero and use_ck_gemm_template(layout, m, n, k):
        CKGemmTemplate.add_ck_gemm_choices(
            choices,
            layout,
            # reorder here because CK expects (x, w, bias) but torch
            # is bias, x, w
            kernel_inputs.nodes(reorder=[1, 2, 0]),
            alpha=alpha,
            beta=beta,
            input_reorder=[2, 0, 1],
        )

    if use_cpp_gemm_template(layout, mat1, mat2):
        CppGemmTemplate.add_choices(
            choices,
            layout,
            kernel_inputs.nodes(),
            alpha=alpha,
            beta=beta,
            has_bias=True,
        )

    node, _ = autotune_select_algorithm(name, choices, kernel_inputs.nodes(), layout)
    return node
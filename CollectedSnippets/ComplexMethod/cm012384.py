def tuned_int_mm(mat1, mat2, *, layout=None):
    # TODO(coconutruben): integrate into MMKernelInputs when all callsites use that
    m, n, k, layout, mat1, mat2 = mm_args(
        mat1, mat2, layout=layout, out_dtype=torch.int32
    )
    name = "int_mm"
    # below is for getting an overview logging info of inductor mms
    counters["aten_mm_info"][f"aten._int_mm_{m}_{n}_{k}"] += 1
    log.info(
        "Tuned aten._int_mm: m=%s, n=%s, k=%s, mat1_dtype=%s, mat2_dtype=%s, output_layout=%s",
        m,
        n,
        k,
        mat1.get_dtype(),
        mat2.get_dtype(),
        layout,
    )

    static_shape, is_nonzero = _is_static_problem(layout)
    use_cutlass = static_shape and is_nonzero and use_cutlass_template(layout, m, n, k)
    choices: list[ChoiceCaller] = []

    # Create MMKernelInputs for Int MM
    kernel_inputs = MMKernelInputs([mat1, mat2], out_dtype=torch.int32)

    # Collect all templates for unified call
    templates_to_use: list[ExternKernelChoice | KernelTemplate] = []
    if use_aten_gemm_kernels():
        templates_to_use.append(aten__int_mm)

    if is_nonzero and use_triton_template(
        layout, enable_int32=True, check_max_autotune=False
    ):
        templates_to_use.append(mm_template)

    # Single unified call for all templates
    choices.extend(
        V.choices.get_template_configs(kernel_inputs, templates_to_use, name)
    )

    if use_cutlass and _use_cutlass_for_op(name):
        CUTLASS3xGemmTemplate.add_cutlass_gemm_choices(
            choices, layout, kernel_inputs.nodes(), fuseable=True, non_fuseable=True
        )

    node, _ = autotune_select_algorithm(name, choices, kernel_inputs.nodes(), layout)
    return node
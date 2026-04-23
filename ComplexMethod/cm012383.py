def tuned_mm(mat1, mat2, out_dtype=None, *, layout=None):
    """
    Lowering for autotuning aten.mm with different backends (Aten, Triton, CUTLASS, etc.)
    """
    if out_dtype is not None:
        input_dtype = mat1.get_dtype()
        torch._check(
            mat2.get_dtype() == input_dtype,
            lambda: "input dtypes must be the same",
        )
        torch._check(
            mat1.get_device().type in ("cuda", "xpu"),
            lambda: "out_dtype is only supported for CUDA or XPU",
        )
        torch._check(
            out_dtype == input_dtype
            or (
                out_dtype == torch.float32
                and input_dtype in (torch.float16, torch.bfloat16)
            ),
            lambda: "out_dtype must be the same as input dtype or fp32 for fp16/bf16 inputs",
        )

    # Lower matmul-related operations (e.g., torch.matmul / torch.bmm / torch.addmm)
    # into native matmul IR using `ops.dot`. When we see a matmul pattern
    # (C[y, x] = A[y, r] * B[r, x]), the core idea is to emulate a broadcasted
    # multiply followed by a sum.
    #
    # For example, given `C = torch.matmul(A, B)`, this can be rewritten as:
    #
    #     Prod = A.unsqueeze(-1) * B.unsqueeze(0)
    #     C = Prod.sum(dim=1)
    #
    # Instead of explicitly using `ops.mul` and `ops.reduction("sum")`, we lower
    # these into `ops.dot` (pointwise) and `ops.reduction("dot")`. These IR nodes
    # are semantically equivalent to the `ops.mul` + `ops.reduction("sum")`
    # combination, but are lowered to `tl.dot` during the code generation phase.
    if use_native_matmul(mat1, mat2):
        mat1 = lowerings[aten.unsqueeze](mat1, -1)
        mat2 = lowerings[aten.unsqueeze](mat2, 0)
        args, kwargs = transform_args(
            args=[mat1, mat2],
            kwargs={},
            broadcast=True,
            type_promotion_kind=None,
            convert_input_to_bool=False,
        )  # Handles broadcasting the arguments

        if inductor_config.triton.codegen_upcast_to_fp32 and mat1.dtype in [
            torch.float16,
            torch.bfloat16,
        ]:

            def _to_dtype(x):
                return ops.to_dtype(x, mat1.dtype, use_compute_types=False)

            args = [make_pointwise(_to_dtype)(x) for x in args]
        mul_pointwise = make_pointwise(ops.dot)(*args)
        dot_reduction = make_reduction("dot")(mul_pointwise, 1)

        return dot_reduction

    # TODO(coconutruben): integrate into MMKernelInputs when all callsites use that
    m, n, k, layout, mat1, mat2 = mm_args(
        mat1, mat2, layout=layout, out_dtype=out_dtype
    )
    static_shape, is_nonzero = _is_static_problem(layout)
    name = "mm"

    # Create MMKernelInputs for standard MM at the top
    kernel_inputs = MMKernelInputs([mat1, mat2], out_dtype=out_dtype)

    # below is for getting an overview logging info of inductor mms
    counters["aten_mm_info"][f"aten.mm_{m}_{n}_{k}"] += 1
    log.info(
        "Tuned aten.mm: m=%s, n=%s, k=%s, mat1_dtype=%s, mat2_dtype=%s, output_layout=%s",
        m,
        n,
        k,
        mat1.get_dtype(),
        mat2.get_dtype(),
        layout,
    )

    choices: list[ChoiceCaller] = []
    static_shape, is_nonzero = _is_static_problem(layout)

    aten_handler: ExternKernelChoice = aten_mm
    aten_extra_kwargs: dict[str, Any] = {}
    if out_dtype is not None:
        aten_handler = aten_mm_dtype
        aten_extra_kwargs = {"out_dtype": out_dtype}

    templates_to_use: list[ExternKernelChoice | KernelTemplate] = []
    kwarg_overrides: dict[str, dict[str, Any]] = {}
    if use_aten_gemm_kernels():
        templates_to_use.append(aten_handler)
        if aten_extra_kwargs:
            kwarg_overrides[aten_handler.uid] = aten_extra_kwargs

    if (
        out_dtype is None
        and is_nonzero
        and use_triton_template(layout, check_max_autotune=True)
    ):
        if use_decompose_k_choice(m, n, k):
            templates_to_use.append(decompose_k_subgraph_template)
        # Triton Templates typically perform very poorly for large K.
        # Its highly unlikely that if we want to use decompose_k, then
        # Triton will ever win.
        #
        # To be conservative we increase this threshold for N/M by 2.
        is_exhaustive = inductor_config.max_autotune_gemm_search_space == "exhaustive"
        if is_exhaustive or not use_decompose_k_choice(m, n, k, threshold_multiple=2):
            templates_to_use.append(mm_template)

            if use_triton_blackwell_tma_template(
                mat1, mat2, output_layout=layout, add_guards=True
            ):
                templates_to_use.append(blackwell_ws_persistent_device_tma_mm_template)
            elif use_triton_tma_template(
                mat1, mat2, output_layout=layout, add_guards=True
            ):
                if torch.version.hip is None:
                    templates_to_use.append(persistent_tma_mm_template)
                else:
                    templates_to_use.append(persistent_mm_template)

        templates_to_use.append(mm_contiguous_subgraph_template)

    choices.extend(
        V.choices.get_template_configs(
            kernel_inputs,
            templates_to_use,
            "mm",
            kwarg_overrides=kwarg_overrides,
        )
    )

    if (
        out_dtype is None
        and is_nonzero
        and use_cutlass_template(layout, m, n, k)
        and _use_cutlass_for_op("mm")
    ):
        CUTLASS3xGemmTemplate.add_cutlass_gemm_choices(
            choices, layout, kernel_inputs.nodes()
        )

    if out_dtype is None and is_nonzero and use_ck_gemm_template(layout, m, n, k):
        CKGemmTemplate.add_ck_gemm_choices(choices, layout, kernel_inputs.nodes())
    if out_dtype is None and is_nonzero and use_ck_tile_gemm_template(layout, m, n, k):
        CKTileGemmTemplate.add_choices(choices, layout, kernel_inputs.nodes())

    if (
        out_dtype is None
        and is_nonzero
        and use_nv_universal_gemm_template(layout, m, n, k, mat1, mat2)
    ):
        from ..codegen.nv_universal_gemm import add_nv_universal_gemm_choices

        add_nv_universal_gemm_choices(choices, layout, kernel_inputs)

    if out_dtype is None and use_cpp_gemm_template(layout, mat1, mat2):
        CppGemmTemplate.add_choices(
            choices,
            layout,
            kernel_inputs.nodes(),
        )

    input_nodes = [mat1, mat2]
    if (
        out_dtype is None
        and is_nonzero
        and use_triton_template(layout)
        and torch._inductor.config.run_autoheuristic(name)
        and is_triton(mat1)
    ):
        always_included = []
        if use_aten_gemm_kernels():
            always_included.append("extern_mm")
        num_choices_before_extra_configs = len(choices)
        choices.extend(
            V.choices.get_template_configs(
                # TODO(coconutruben): remove once we deprecate ah
                # mm-extra is a hack to keep the ah functionality alive
                # while we transition to the unified kwargs retrieval
                kernel_inputs,
                [mm_template],
                "mm-ah",
            )
        )

        # using AutoHeuristic for ranking
        ah_choices = mm_autoheuristic(
            mat1,
            mat2,
            m,
            n,
            k,
            choices,
            name,
            input_nodes,
            mm_operations(),
            None,
            top_k=10,
            always_included=always_included,
        )
        if not torch._inductor.config.collect_autoheuristic(name):
            # if we are collecting data, we do not want to modify choices
            if ah_choices is not None and len(ah_choices) > 0:
                # the order in which autoheuristic returns choices is not the same as
                # as the order of choices, which affects things like epilogue fusion.
                # once epilogue fusion benchmarks choices in sorted order, I think we can
                # just use the order returned by autoheuristic
                choices = [choice for choice in choices if choice in ah_choices]
            else:
                choices = choices[:num_choices_before_extra_configs]

    if out_dtype is None:
        for k in inductor_config.external_matmul:
            choices.append(
                lazy_register_extern_choice(k).bind(kernel_inputs.nodes(), layout)
            )

    best_config_future = None
    if out_dtype is None and torch._inductor.config.remote_gemm_autotune_cache:
        # Purposely not awaiting the future here - this kicks off the best config lookup at lowering time
        # The future will be awaited at scheduling time in select_algorithm.py
        best_config_future = gen_best_config(mat1, mat2)

    if box := distributed_autotune.maybe_autotune_remote(
        name, choices, kernel_inputs.nodes(), layout
    ):
        return box

    node, _ = autotune_select_algorithm(
        name,
        choices,
        kernel_inputs.nodes(),
        layout,
        best_config_future=best_config_future,
    )
    return node
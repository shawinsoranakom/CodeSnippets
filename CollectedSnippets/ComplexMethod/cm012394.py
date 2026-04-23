def _tuned_grouped_mm_common(
    operator_name: str,
    algorithm_name: str,
    extern_kernel_choice: ExternKernelChoice,
    kernel_template: TritonTemplate,
    mat_a: TensorBox,
    mat_b: TensorBox,
    scale_a: TensorBox | None = None,
    scale_b: TensorBox | None = None,
    offs: TensorBox | None = None,
    bias: TensorBox | None = None,
    scale_result: TensorBox | None = None,
    out_dtype: torch.dtype | None = None,
    use_fast_accum: bool | None = None,
    layout: Layout | None = None,
) -> TensorBox:
    assert (scale_a is None) == (scale_b is None)
    assert scale_result is None or scale_a is not None

    m1_size, m2_size, layout, mat_a, mat_b, offs = grouped_mm_args(
        mat_a, mat_b, offs, layout=layout, out_dtype=out_dtype
    )
    counters["aten_mm_info"][operator_name] += 1
    log_message = f"Tuned {operator_name}: mat1_shape=%s, mat2_shape=%s, mat1_dtype=%s, mat2_dtype=%s, output_layout=%s"
    log.info(
        log_message,
        m1_size,
        m2_size,
        mat_a.get_dtype(),
        mat_b.get_dtype(),
        layout,
    )

    if scale_a is not None and scale_b is not None:
        check_supported_striding(mat_a, mat_b)

    # workaround for Inductor not supporting optional tensor input arguments
    input_nodes: list[Any] = [mat_a, mat_b]
    if scale_a is not None:
        input_nodes.append(realize_inputs(scale_a))
    if scale_b is not None:
        input_nodes.append(realize_inputs(scale_b))
    if offs is not None:
        input_nodes.append(realize_inputs(offs))

    if use_fast_accum is None:
        aten_choice = extern_kernel_choice.bind(
            input_nodes,
            layout,
            out_dtype=out_dtype,
        )
    else:
        aten_choice = extern_kernel_choice.bind(
            input_nodes,
            layout,
            out_dtype=out_dtype,
            use_fast_accum=use_fast_accum,
        )
    if use_fast_accum is None:
        use_fast_accum = False

    choices: list[ChoiceCaller] = []
    if use_aten_gemm_kernels():
        choices.append(aten_choice)

    _, is_nonzero = _is_static_problem(layout)

    # Checking only for the equality of corresponding dims of
    # multiplicands here, relying on meta function checks for
    # everything else.
    if len(m1_size) == 2:
        if len(m2_size) == 2:
            m, k1 = m1_size
            k2, n = m2_size

            g = offs.get_size()[0]
            k = V.graph.sizevars.check_equals(k1, k2)
            a_is_2d, b_is_2d = True, True
        else:
            g1 = offs.layout.size[0]
            m, k1 = m1_size
            g2, k2, n = m2_size
            g = V.graph.sizevars.check_equals_and_simplify(g1, g2)
            k = V.graph.sizevars.check_equals(k1, k2)
            a_is_2d, b_is_2d = True, False
    else:
        if len(m2_size) == 2:
            g1 = offs.layout.size[0]
            g2, m, k1 = m1_size
            k2, n = m2_size
            g = V.graph.sizevars.check_equals_and_simplify(g1, g2)
            k = V.graph.sizevars.check_equals(k1, k2)
            a_is_2d, b_is_2d = False, True
        else:
            g1, m, k1 = m1_size
            g2, k2, n = m2_size
            g = V.graph.sizevars.check_equals_and_simplify(g1, g2)
            k = V.graph.sizevars.check_equals(k1, k2)
            a_is_2d, b_is_2d = False, False

    if (
        is_nonzero
        and use_triton_template(layout)
        and can_use_triton_kernel(mat_a, mat_b, offs, bias, scale_result)
    ):
        scaled = scale_a is not None

        a_is_k_major = mat_a.get_stride()[-1] == 1
        b_is_k_major = mat_b.get_stride()[-2] == 1

        triton_has_make_tensor_descriptor = hasattr(tl, "make_tensor_descriptor")
        triton_has_experimental_make_tensor_descriptor = hasattr(
            tl, "_experimental_make_tensor_descriptor"
        )
        use_tma_load = (
            triton_has_make_tensor_descriptor
            or triton_has_experimental_make_tensor_descriptor
        )
        kwargs = {
            "SCALED": scaled,
            "A_IS_2D": a_is_2d,
            "B_IS_2D": b_is_2d,
            "A_IS_K_MAJOR": a_is_k_major,
            "B_IS_K_MAJOR": b_is_k_major,
            "USE_FAST_ACCUM": use_fast_accum,
            "NUM_SMS": get_num_sms(),
            "USE_TMA_LOAD": use_tma_load,
            "USE_EXPERIMENTAL_MAKE_TENSOR_DESCRIPTOR": triton_has_experimental_make_tensor_descriptor,
        }

        for config in early_config_prune(
            g, m, mat_a.dtype.itemsize, grouped_mm_configs(), kwargs
        ):
            kernel_template.maybe_append_choice(
                choices,
                input_nodes=input_nodes,
                layout=layout,
                num_stages=config.num_stages,
                num_warps=config.num_warps,
                **kwargs,
                **config.kwargs,
            )

    if use_blackwell_cutedsl_grouped_mm(
        mat_a, mat_b, layout, a_is_2d, b_is_2d, offs, bias, scale_result
    ):
        for config in get_groupgemm_configs():
            kwargs = dict(
                ACC_DTYPE="cutlass.Float32",
            )

            cutedsl_grouped_mm_template.maybe_append_choice(
                choices,
                input_nodes=input_nodes,
                layout=layout,
                **kwargs,
                **asdict(config),
            )

    if (
        is_nonzero
        and a_is_2d
        and not b_is_2d
        and offs is not None
        and use_nv_universal_gemm_template(layout, m, n, k, mat_a, mat_b, offs, g)
    ):
        from torch._inductor.codegen.nv_universal_gemm.nv_universal_gemm import (
            add_nv_universal_grouped_gemm_choices,
        )

        add_nv_universal_grouped_gemm_choices(
            choices,
            layout,
            input_nodes,
            accumulator_type=torch.float32,
        )

    input_gen_fns = {}
    if offs is not None:
        input_offs_idx = 2 if scale_a is None else 4
        alignment = 16 // mat_a.dtype.itemsize
        input_gen_fns[input_offs_idx] = lambda x: create_offsets(
            x, a_is_2d, b_is_2d, m, n, k, alignment
        )
    node, _ = autotune_select_algorithm(
        algorithm_name, choices, input_nodes, layout, input_gen_fns=input_gen_fns
    )
    return node
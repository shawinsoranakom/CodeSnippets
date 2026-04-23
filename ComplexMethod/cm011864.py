def grouped_gemm_lowering(
    x: TensorBox,
    w: list[TensorBox],
    b: list[TensorBox],
    attr=None,
    scalars=None,
    algorithm=None,
    layout=None,
):
    x_size = x.get_size()
    if len(x_size) > 2:
        # GEMM template needs 2D input, normalize input shape here
        x = view(x, [-1, x_size[-1]])
    num_gemm = len(w)

    assert config.max_autotune or config.max_autotune_gemm
    # pyrefly: ignore [bad-assignment]
    b = [bias if bias is None else ir.ExternKernel.realize_input(bias) for bias in b]

    choices: list[ChoiceCaller] = []
    *_, layout, x, _ = mm_args(x, permute(w[0], [1, 0]), layout=layout)

    kwargs = {
        "has_bias": [bias is not None for bias in b],
        "trans_w": True,
        "epilogue_creator": None,
        "act_mapping": dict.fromkeys(range(num_gemm), x),
    }

    input_nodes = [x, *w]
    input_nodes.extend([bias for bias in b if bias is not None])

    CppGroupedGemmTemplate.add_choices(
        choices,
        layout,
        input_nodes,
        **kwargs,  # type: ignore[arg-type]
    )

    assert len(choices) != 0
    result, _ = autotune_select_algorithm(
        "grouped_gemm",
        choices,
        input_nodes,
        layout,
    )
    template_buf = result.data.data
    return_bufs = [
        ir.MultiOutput(layout, template_buf, [(list, gemm_idx)])
        for gemm_idx in range(num_gemm)
    ]
    # pyrefly: ignore [bad-argument-type]
    template_buf.layout = ir.MultiOutputLayout(device=input_nodes[0].get_device())
    template_buf.outputs = return_bufs
    return_tensors = [
        ir.TensorBox.create(return_bufs[gemm_idx]) for gemm_idx in range(num_gemm)
    ]
    if len(x_size) > 2:
        for gemm_idx in range(num_gemm):
            return_tensors[gemm_idx] = view(
                return_tensors[gemm_idx],  # type: ignore[arg-type]
                (*x_size[:-1], return_tensors[gemm_idx].get_size()[-1]),
            )
    return return_tensors
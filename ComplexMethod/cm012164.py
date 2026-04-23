def _get_sfdp_patterns(input_device: torch.device | None = None):
    from .joint_graph import patterns

    if input_device:
        device = str(input_device)
    else:
        if torch.cuda.is_available():
            # workaround https://github.com/pytorch/pytorch/issues/97894
            device = "cuda"
        elif torch.xpu.is_available():
            device = "xpu"
        else:
            device = "cpu"

    # sizes/values don't actually matter for initial trace
    # once we get a possible match we re-trace with the actual values and verify the match still holds
    g_inp = functools.partial(
        torch.empty, (2, 4, 8, 16), device=device, requires_grad=True
    )
    # non-contiguous input to cover more patterns.
    gn_inp = functools.partial(
        torch.empty_strided,
        (2, 6, 16, 8),
        (2304, 128, 1, 16),
        device=device,
        requires_grad=True,
    )
    # attn_mask
    b_inp = functools.partial(torch.empty, (1, 1, 8, 8), device=device)
    m_inp = functools.partial(torch.empty, (2, 1, 1, 4), device=device)
    # need 2d attn_mask to generate patterns with view op
    m_inp_2d = functools.partial(torch.empty, (2, 4), device=device)
    # inv_scale
    c_inp = functools.partial(torch.tensor, 2.0, device=device)
    # workaround https://github.com/pytorch/pytorch/issues/97894
    # 0.113377 is a "magic" value that lets us recover the lost input arg relationship
    d = {"dropout_p": 0.113377}
    s = {"inv_scale": 0.66666}
    sd = {"inv_scale": 0.66666, "dropout_p": 0.113377}

    # we could also generate all these patterns in 3d.. TODO
    g_3d_inp = functools.partial(
        torch.empty, (1024, 128, 128), device=device, requires_grad=True
    )

    # reshape in matmul decomposition generates a clone when batch_size>1 due to the memory layout change.
    # however when batch_size=1, reshape does not change the memory layout, so clone would not be generated.
    # here we need to trace with input of batch_size=1 to generate a pattern graph without clone.
    g_bs1_inp = functools.partial(
        torch.empty, (1, 4, 8, 16), device=device, requires_grad=True
    )
    m_bs1_inp = functools.partial(torch.empty, (1, 1, 1, 4), device=device)

    # softmax will generate a dtype conversion on inputs if they are in half,
    # but will not in float, so we generate a pattern for both
    for dtype in [torch.float, torch.half]:
        g = functools.partial(g_inp, dtype=dtype)
        gn = functools.partial(gn_inp, dtype=dtype)
        b = functools.partial(b_inp, dtype=dtype)
        b_float = functools.partial(b_inp, dtype=torch.float)
        b_bool = functools.partial(b_inp, dtype=torch.bool)
        m = functools.partial(m_inp, dtype=dtype)
        m_float = functools.partial(m_inp, dtype=torch.float)
        m_bool = functools.partial(m_inp, dtype=torch.bool)
        m_2d = functools.partial(m_inp_2d, dtype=dtype)
        c = functools.partial(c_inp, dtype=dtype)
        g_3d = functools.partial(g_3d_inp, dtype=dtype)
        g_bs1 = functools.partial(g_bs1_inp, dtype=dtype)
        m_bs1 = functools.partial(m_bs1_inp, dtype=dtype)
        m_bs1_float = functools.partial(m_bs1_inp, dtype=torch.float)
        m_bs1_bool = functools.partial(m_bs1_inp, dtype=torch.bool)

        candidates = [
            (
                _sfdp_pattern_1,
                _sfdp_replacement_1,
                [g(), g(), g(), c()],
                {},
                _sfdp_extra_check(aten.div.Tensor),
            ),
            (
                _sfdp_pattern_2,
                _sfdp_replacement_2,
                [g(), g(), g(), c()],
                {},
                _sfdp_extra_check(aten.mul.Tensor),
            ),
            (
                _sfdp_pattern_3,
                _sfdp_replacement_3,
                [g(), g(), g(), c()],
                d,
                _sfdp_extra_check(aten.div.Tensor),
            ),
            (
                _sfdp_pattern_4,
                _sfdp_replacement_4,
                [g(), g(), g(), c()],
                d,
                _sfdp_extra_check(aten.mul.Tensor),
            ),
            (
                _sfdp_pattern_5,
                _sfdp_replacement_5,
                [g(), g(), g(), b()],
                s,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_6,
                _sfdp_replacement_6,
                [g(), g(), g(), b()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_7,
                _sfdp_replacement_7,
                [g(), g(), g()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_8,
                _sfdp_replacement_8,
                [g(), g(), g()],
                s,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_9,
                _sfdp_replacement_9,
                [g(), g(), g()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_10,
                _sfdp_replacement_10,
                [g(), g(), g()],
                s,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_11,
                _sfdp_replacement_11,
                [g(), g(), g(), c()],
                {},
                _sfdp_extra_check(aten.div.Tensor),
            ),
            (
                _sfdp_pattern_12,
                _sfdp_replacement_12,
                [g(), g(), g(), c()],
                d,
                _sfdp_extra_check(aten.div.Tensor),
            ),
            (
                _sfdp_pattern_13,
                _sfdp_replacement_13,
                [g_3d(), g_3d(), g_3d()],
                d,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_14,
                _sfdp_replacement_14,
                [g(), g(), g(), m(), c()],
                {},
                _sfdp_extra_check(aten.div.Tensor),
            ),
            (
                _sfdp_pattern_15,
                _sfdp_replacement_15,
                [g(), g(), g(), m_2d(), c()],
                {},
                _sfdp_extra_check(aten.div.Tensor),
            ),
            # disable_cuda only for NVIDIA CUDA (not ROCm) due to Bert accuracy issue
            (
                _sfdp_pattern_16,
                _sfdp_replacement_16,
                [g(), g(), g(), m(), c()],
                d,
                _sfdp_extra_check(
                    aten.div.Tensor, disable_cuda=torch.version.hip is None
                ),
            ),
            (
                _sfdp_pattern_16,
                _sfdp_replacement_16,
                [g_bs1(), g_bs1(), g_bs1(), m_bs1(), c()],
                d,
                _sfdp_extra_check(
                    aten.div.Tensor, disable_cuda=torch.version.hip is None
                ),
            ),
            (
                _sfdp_pattern_17,
                _sfdp_replacement_17,
                [g(), g(), g(), m_2d(), c()],
                d,
                _sfdp_extra_check(aten.div.Tensor),
            ),
            (
                _sfdp_pattern_18,
                _sfdp_replacement_18,
                [g(), g(), g(), m_bool()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_18,
                _sfdp_replacement_18,
                [g_bs1(), g_bs1(), g_bs1(), m_bs1_bool()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_19,
                _sfdp_replacement_19,
                [g(), g(), g(), b_bool(), b_float()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_20,
                _sfdp_replacement_20,
                [g(), g(), g(), m_2d()],
                sd,
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_21,
                _sfdp_replacement_21,
                [g(), g(), g(), m_float()],
                {},
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_21,
                _sfdp_replacement_21,
                [g_bs1(), g_bs1(), g_bs1(), m_bs1_float()],
                {},
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_22,
                _sfdp_replacement_22,
                [g(), g(), g(), m_float()],
                {},
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_22,
                _sfdp_replacement_22,
                [g_bs1(), g_bs1(), g_bs1(), m_bs1_float()],
                {},
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_23,
                _sfdp_replacement_23,
                [g(), g(), g()],
                {},
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_23,
                _sfdp_replacement_23,
                [g_bs1(), g_bs1(), g_bs1()],
                {},
                _sfdp_params_check,
            ),
            (
                _sfdp_pattern_24,
                _sfdp_replacement_24,
                [g(), g(), g(), b_float()],
                {},
                _sfdp_extra_check,
            ),
            (
                _sfdp_pattern_25,
                _sfdp_replacement_25,
                [g(), g(), g(), m()],
                d,
                _sfdp_extra_check(disable_cuda=True),
            ),
            (
                _sfdp_pattern_25,
                _sfdp_replacement_25,
                [g_bs1(), g_bs1(), g_bs1(), m_bs1()],
                d,
                _sfdp_extra_check(disable_cuda=True),
            ),
            (
                _sfdp_pattern_26,
                _sfdp_replacement_26,
                [g(), g(), g(), m()],
                d,
                _sfdp_extra_check(disable_cuda=True),
            ),
            (
                _sfdp_pattern_26,
                _sfdp_replacement_26,
                [g_bs1(), g_bs1(), g_bs1(), m_bs1()],
                d,
                _sfdp_extra_check(disable_cuda=True),
            ),
            (
                _sfdp_pattern_27,
                _sfdp_replacement_27,
                [g(), g(), g()],
                d,
                _sfdp_extra_check(disable_cuda=True),
            ),
            (
                _sfdp_pattern_27,
                _sfdp_replacement_27,
                [g_bs1(), g_bs1(), g_bs1()],
                d,
                _sfdp_extra_check(disable_cuda=True),
            ),
            (
                _sfdp_pattern_28,
                _sfdp_replacement_28,
                [gn(), gn(), gn(), c()],
                d,
                _sfdp_extra_check(aten.mul.Tensor),
            ),
        ]
        mask_fp32_patterns = ["pattern_16"]
        if dtype == torch.half:
            # Add inputs of bf16 q/k/v and fp32 mask, for models like albert.
            candidates.append(
                (
                    _sfdp_pattern_16,
                    _sfdp_replacement_16,
                    [g(), g(), g(), m_float(), c()],
                    d,
                    # disable_cuda only for NVIDIA CUDA (not ROCm) due to Bert accuracy issue
                    _sfdp_extra_check(
                        aten.div.Tensor, disable_cuda=torch.version.hip is None
                    ),
                )
            )
            candidates.append(
                (
                    _sfdp_pattern_16,
                    _sfdp_replacement_16,
                    [g_bs1(), g_bs1(), g_bs1(), m_bs1_float(), c()],
                    d,
                    # disable_cuda only for NVIDIA CUDA (not ROCm) due to Bert accuracy issue
                    _sfdp_extra_check(
                        aten.div.Tensor, disable_cuda=torch.version.hip is None
                    ),
                )
            )

        for pattern, replacement, args, workaround, extra_check in candidates:
            # XXX: when adding a new pattern, re-run `gen_attention_patterns` so the pattern
            # gets serialized to a python file and does not require tracing at runtime.
            assert isinstance(workaround, dict)
            name = pattern.__name__

            if dtype != torch.float:
                name += "_half"
                if (
                    any(p in name for p in mask_fp32_patterns)
                    and args[3].dtype == torch.float32
                ):
                    name += "_mask_fp32"
            if args[0].size(0) == 1:
                name += "_bs1"

            training_name = name + "_training"
            yield (
                training_name,
                {
                    "search_fn": pattern,
                    "replace_fn": replacement,
                    "example_inputs": args,
                    "trace_fn": joint_fwd_bwd,
                    "pass_dicts": patterns,
                    "extra_check": extra_check,
                    "scalar_workaround": workaround,
                    "skip_duplicates": True,
                },
            )
            inference_workaround = {}
            if workaround:
                assert len(workaround) <= 2
                if "inv_scale" in workaround:
                    inference_workaround["inv_scale"] = workaround["inv_scale"]
                if "dropout_p" in workaround:
                    # functools.partial insufficient because we look at signature downstream
                    pattern = partialize_and_update_signature(pattern, dropout_p=0.0)
                    replacement = partialize_and_update_signature(
                        replacement, dropout_p=0.0
                    )

            inference_name = name + "_inference"
            yield (
                inference_name,
                {
                    "search_fn": pattern,
                    "replace_fn": replacement,
                    "example_inputs": args,
                    "trace_fn": fwd_only,
                    "pass_dicts": patterns,
                    "extra_check": extra_check,
                    "scalar_workaround": inference_workaround,
                    # with dropout turned into clone, we end up with a number of
                    # semantically identical graphs
                    "skip_duplicates": True,
                },
            )
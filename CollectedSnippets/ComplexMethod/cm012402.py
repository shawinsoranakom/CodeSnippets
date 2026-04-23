def flex_attention(
    query,
    key,
    value,
    subgraph,
    block_mask,
    scale,
    kernel_options: dict[str, Any],
    score_mod_other_buffers,
    mask_mod_other_buffers,
):
    """The main lowering for the flex_attention hop
    This can currently lower to one of 3 templates:
    1. Base Triton Template
    2. Flex Decode Triton Template
    3. Cpu specific CPP template
    """
    if query.get_device().type == "cpu":
        return lower_cpu(
            query,
            key,
            value,
            subgraph,
            block_mask,
            scale,
            kernel_options,
            score_mod_other_buffers,
            mask_mod_other_buffers,
        )
    # below is cuda path if device is not cpu
    # tl.dot does not support embedding size less than 16
    small_dqk = V.graph.sizevars.evaluate_expr(sympy.Lt(query.get_size()[-1], 16))
    small_dv = V.graph.sizevars.evaluate_expr(sympy.Lt(value.get_size()[-1], 16))
    if small_dqk or small_dv:
        raise NotImplementedError(
            f"NYI: embedding dimension of the query, key, and value must be "
            f"at least 16 but got E={query.get_size()[-1]} and Ev={value.get_size()[-1]}"
        )

    (
        _,  # q_length
        _,  # kv_length
        kv_num_blocks,
        kv_indices,
        full_kv_num_blocks,
        full_kv_indices,
        q_num_blocks,
        q_indices,
        full_q_num_blocks,
        full_q_indices,
        SPARSE_Q_BLOCK_SIZE,
        SPARSE_KV_BLOCK_SIZE,
        mask_graph,
    ) = block_mask

    kernel_options, backend = _sanitize_kernel_options_for_triton(kernel_options)

    # Early check for FLASH backend: detect unsupported captured scalars before
    # building subgraph buffers (which can trigger unbacked_bindings errors)
    if backend == "FLASH":
        from .flex_flash_attention import _has_unsupported_captured_scalars

        if _has_unsupported_captured_scalars(
            score_mod_other_buffers, mask_mod_other_buffers
        ):
            raise RuntimeError(
                "BACKEND='FLASH' but flash attention cannot be used: "
                "NYI: score_mod or mask_mod captures a dynamic scalar (SymInt/SymFloat). "
                "The FLASH backend cannot inline symbolic values into the CuteDSL template. "
                "Workarounds: use BACKEND='TRITON', compile with dynamic=False, or pass the "
                "value as a tensor on device instead of capturing a Python scalar."
            )

    placeholder_inps = [
        create_placeholder(name, dtype, query.get_device())
        for name, dtype in [
            ("score", query.get_dtype()),
            ("b", torch.int32),
            ("h", torch.int32),
            ("m", torch.int32),
            ("n", torch.int32),
        ]
    ]
    subgraph_buffer = build_subgraph_buffer(
        placeholder_inps + list(score_mod_other_buffers), subgraph
    )
    freeze_irnodes(subgraph_buffer)

    mask_graph_placeholder_inps = [
        create_placeholder(name, dtype, query.get_device())
        for name, dtype in [
            ("b", torch.int32),
            ("h", torch.int32),
            ("m", torch.int32),
            ("n", torch.int32),
        ]
    ]
    mask_graph_buffer = build_subgraph_buffer(
        mask_graph_placeholder_inps + list(mask_mod_other_buffers), mask_graph
    )
    freeze_irnodes(mask_graph_buffer)
    # Mark symbols in custom kernel options as static shapes and add guards.
    kernel_options = {
        k: V.graph.sizevars.guard_int(v) if isinstance(v, sympy.Symbol) else v
        for k, v in kernel_options.items()
    }
    kernel_options.setdefault("FLOAT32_PRECISION", get_float32_precision())
    enable_gqa = V.graph.sizevars.evaluate_expr(
        sympy.Ne(query.get_size()[1], key.get_size()[1]),
    )

    can_use_decode = _use_flex_decoding(
        query, kv_indices, value, kernel_options, enable_gqa
    )
    use_decode = (backend == "TRITON_DECODE") or (backend == "AUTO" and can_use_decode)

    if backend == "TRITON_DECODE" and not can_use_decode:
        raise RuntimeError(
            "BACKEND='TRITON_DECODE' was specified but flex_decoding cannot be used for this input. "
            "flex_decoding is only available for short sequence lengths with specific configurations."
        )

    if use_decode:
        return create_flex_decoding_kernel(
            query,
            key,
            value,
            block_mask,
            scale,
            kernel_options,
            subgraph_buffer,
            mask_graph_buffer,
            score_mod_other_buffers,
            mask_mod_other_buffers,
        )

    (
        query,
        key,
        value,
        kv_num_blocks,
        kv_indices,
        full_kv_num_blocks,
        full_kv_indices,
        q_num_blocks,
        q_indices,
        full_q_num_blocks,
        full_q_indices,
    ) = maybe_realize(
        [
            query,
            key,
            value,
            kv_num_blocks,
            kv_indices,
            full_kv_num_blocks,
            full_kv_indices,
            q_num_blocks,
            q_indices,
            full_q_num_blocks,
            full_q_indices,
        ]
    )

    if _use_flex_flash_attention(
        subgraph,
        mask_graph,
        kernel_options,
        num_score_mod_placeholders=len(placeholder_inps),
        backend=backend,
    ):
        return create_flex_flash_attention_kernel(
            query,
            key,
            value,
            block_mask,
            scale,
            kernel_options,
            subgraph_buffer,
            mask_graph_buffer,
            score_mod_other_buffers,
            mask_mod_other_buffers,
            kv_num_blocks,
            kv_indices,
            full_kv_num_blocks,
            full_kv_indices,
            SPARSE_Q_BLOCK_SIZE,
            SPARSE_KV_BLOCK_SIZE,
            mask_graph=mask_graph,
            subgraph=subgraph,
        )

    score_mod_other_buffers = maybe_realize(score_mod_other_buffers)
    mask_mod_other_buffers = maybe_realize(mask_mod_other_buffers)

    freeze_irnodes(score_mod_other_buffers)
    freeze_irnodes(mask_mod_other_buffers)

    Bq, Hq, seq_len_q, qk_head_dim = query.get_size()
    Bkv, Hkv, seq_len_kv, v_head_dim = value.get_size()
    assert V.graph.sizevars.evaluate_expr(sympy.Eq(Bq, Bkv) | sympy.Eq(Bkv, 1)), (
        f"Bq and Bkv must broadcastable. Got Bq={Bq} and Bkv={Bkv}"
    )
    assert V.graph.sizevars.evaluate_expr(sympy.Gt(seq_len_q, 0)), (
        "Query length must be greater than 0"
    )
    assert V.graph.sizevars.evaluate_expr(sympy.Gt(seq_len_kv, 0)), (
        "Key length must be greater than 0"
    )

    B = Bq

    seq_q_divisible = V.graph.sizevars.statically_known_true(
        sympy.Eq(Mod(seq_len_q, 128), 0)
    )
    seq_kv_divisible = V.graph.sizevars.statically_known_true(
        sympy.Eq(Mod(seq_len_kv, 128), 0)
    )
    if seq_q_divisible and seq_kv_divisible:
        kernel_options.setdefault("IS_DIVISIBLE", True)
    else:
        kernel_options.setdefault("IS_DIVISIBLE", False)

    # NB it is okay that the v_head_dim is different
    # We are using these to match fill order of the output.
    q_strides = query.get_stride()
    # Construct output layout with strides matching the query.
    out_size = [B, Hq, seq_len_q, v_head_dim]
    out_strides = infer_dense_strides(out_size, q_strides)

    layout = FixedLayout(
        query.get_device(),
        query.get_dtype(),
        [B, Hq, seq_len_q, v_head_dim],
        stride=[sympy.sympify(s) for s in out_strides],
    )
    # see NOTE:[TritonTemplates with multiple outputs]
    logsumexp_shape = [B, Hq, seq_len_q]
    logsumexp = empty_strided(
        logsumexp_shape,
        None,
        dtype=torch.float32,  # The logsumexp is always stored in fp32 regardless of the input dtype
        device=query.get_device(),
    )
    max_scores = empty_strided(
        logsumexp_shape,  # Same shape as logsumexp
        None,
        dtype=torch.float32,  # The max scores are always stored in fp32 regardless of the input dtype
        device=query.get_device(),
    )
    kernel_options.setdefault("SM_SCALE", scale)

    # Determine GQA broadcast factor.
    gqa_shared_heads = FloorDiv(Hq, Hkv)
    kernel_options.setdefault("GQA_SHARED_HEADS", gqa_shared_heads)

    # Inside of Triton kernel, only apply partial masking if partial blocks are computed.
    # full_kv_num_blocks is None if partial blocks are not computed
    has_full_blocks = full_kv_num_blocks is not None
    kernel_options.setdefault("HAS_FULL_BLOCKS", has_full_blocks)
    if not has_full_blocks:
        full_kv_num_blocks, full_kv_indices = (
            empty(0, device=query.get_device()) for _ in range(2)
        )

    set_head_dim_values(kernel_options, qk_head_dim, v_head_dim, V.graph.sizevars)

    choices: list[Any] = []

    dtype = query.get_dtype()
    head_dim = V.graph.sizevars.guard_int(query.get_size()[-1])
    configs: list[FlexConfig] = V.choices.get_flex_attention_fwd_configs(
        head_dim, dtype, query.get_device().type
    )

    # Mark SPARSE_KV_BLOCK_SIZE & SPARSE_Q_BLOCK_SIZE as static shapes and add guards.
    SPARSE_KV_BLOCK_SIZE = V.graph.sizevars.guard_int(SPARSE_KV_BLOCK_SIZE)
    SPARSE_Q_BLOCK_SIZE = V.graph.sizevars.guard_int(SPARSE_Q_BLOCK_SIZE)

    # Note, we don't need to pass in the captured buffers explicitly
    # because they're implicitly added by the score_mod function
    # We do need to explicitly pass it in for autotuning though.
    original_kernel_options = kernel_options.copy()
    # Default config for warp specialization
    num_consumer_groups, num_buffers_warp_spec = 0, 0

    for conf in configs:
        cur_kernel_options = original_kernel_options.copy()
        # Performance tuning
        # Triton parameters
        # Remove prefix for forward kernels options and delete backward kernel options.
        for k in list(cur_kernel_options.keys()):
            if k.startswith("fwd_"):
                v = cur_kernel_options.pop(k)
                cur_kernel_options[k[4:]] = v
            if k.startswith("bwd_"):
                cur_kernel_options.pop(k)
        cur_kernel_options.setdefault("num_stages", conf.num_stages)
        cur_kernel_options.setdefault("num_warps", conf.num_warps)
        if cur_kernel_options.get("num_consumer_groups", False):
            cur_kernel_options.setdefault("num_consumer_groups", num_consumer_groups)
            cur_kernel_options.setdefault(
                "num_buffers_warp_spec", num_buffers_warp_spec
            )

        # Intel GPU enables TMA by default
        cur_kernel_options.setdefault("USE_TMA", bool(torch.xpu.is_available()))

        if cur_kernel_options["USE_TMA"] and not can_use_tma(query, key, value):
            cur_kernel_options["USE_TMA"] = False

        cur_kernel_options.setdefault("BLOCK_M", conf.block_m)
        cur_kernel_options.setdefault("BLOCK_N", conf.block_n)
        # Blocksparse options
        cur_kernel_options.setdefault("SPARSE_Q_BLOCK_SIZE", SPARSE_Q_BLOCK_SIZE)
        cur_kernel_options.setdefault("SPARSE_KV_BLOCK_SIZE", SPARSE_KV_BLOCK_SIZE)

        if (
            cur_kernel_options["SPARSE_KV_BLOCK_SIZE"] % cur_kernel_options["BLOCK_N"]
            != 0
            or cur_kernel_options["SPARSE_Q_BLOCK_SIZE"] % cur_kernel_options["BLOCK_M"]
            != 0
        ):
            if len(configs) == 1:
                raise ValueError(
                    f"Q and KV block size must be divisible by BLOCK_M and BLOCK_N. We "
                    f"got Q_BLOCK_SIZE={cur_kernel_options['SPARSE_Q_BLOCK_SIZE']} and "
                    f"KV_BLOCK_SIZE={cur_kernel_options['SPARSE_KV_BLOCK_SIZE']}."
                )
            continue

        # ROCm specific kernargs
        for attrib in ["kpack", "matrix_instr_nonkdim", "waves_per_eu"]:
            if hasattr(conf, attrib):
                cur_kernel_options[attrib] = getattr(conf, attrib)

        error = flex_attention_template.maybe_append_choice(
            choices=choices,
            input_nodes=[
                query,
                key,
                value,
                logsumexp,
                max_scores,
                kv_num_blocks,
                kv_indices,
                full_kv_num_blocks,
                full_kv_indices,
            ],
            layout=layout,
            subgraphs=[
                subgraph_buffer,
                mask_graph_buffer,
            ],
            mutated_inputs=[
                logsumexp,
                max_scores,
            ],
            call_sizes=query.get_size(),
            **cur_kernel_options,
        )
        if error is not None and len(configs) == 1:
            raise error
    inputs_for_autotuning = (
        [
            query,
            key,
            value,
            logsumexp,
            max_scores,
            kv_num_blocks,
            kv_indices,
            full_kv_num_blocks,
            full_kv_indices,
        ]
        + list(score_mod_other_buffers)
        + list(mask_mod_other_buffers)
    )
    input_gen_fns = {
        5: create_num_blocks_fake_generator(kv_indices),
        6: create_indices_fake,
        7: create_num_blocks_fake_generator(full_kv_indices),
        8: create_indices_fake,
    }

    out, _ = autotune_select_algorithm(
        "flex_attention",
        choices,
        # Need to filter out symbols since there is an invariant
        # that all input_nodes are of type IRNode
        [x for x in inputs_for_autotuning if isinstance(x, torch._inductor.ir.IRNode)],
        layout,
        input_gen_fns=input_gen_fns,
    )

    # need subgraph inputs and outputs to analyze all symints used in flex attention
    out.data.data.subgraph_inps = list(score_mod_other_buffers) + list(
        mask_mod_other_buffers
    )
    out.data.data.subgraph_outs = get_fwd_subgraph_outputs(
        subgraph_buffer, mask_graph_buffer
    )

    return (out, logsumexp, max_scores)
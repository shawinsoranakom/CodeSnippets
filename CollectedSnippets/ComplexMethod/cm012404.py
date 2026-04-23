def flex_attention_backward(*args, **kwargs):
    """Lowering for the flex_attention_backward op in triton"""
    (
        query,
        key,
        value,
        out,
        logsumexp,
        grad_out,
        grad_logsumexp,
        fw_graph,
        joint_graph,
        block_mask,
        scale,
        kernel_options,
        score_mod_other_buffers,
        mask_mod_other_buffers,
    ) = args
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

    (
        query,
        key,
        value,
        logsumexp,
        grad_out,
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
            logsumexp,
            grad_out,
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

    device = query.get_device()
    dtype = query.get_dtype()
    Bq, Hq, seq_len_q, qk_head_dim = query.get_size()
    Bkv, Hkv, seq_len_kv, v_head_dim = value.get_size()

    assert V.graph.sizevars.evaluate_expr(sympy.Eq(Bq, Bkv) | sympy.Eq(Bkv, 1)), (
        f"Bq and Bkv must broadcastable. Got Bq={Bq} and Bkv={Bkv}"
    )

    kernel_options, backend = _sanitize_kernel_options_for_triton(kernel_options)
    # Add check for mixed dtypes
    if query.dtype != key.dtype or query.dtype != value.dtype:
        raise ValueError(
            f"Backward pass with mixed query, key, and value dtype is not supported, "
            f"got query.dtype={query.dtype}, key.dtype={key.dtype}, "
            f"and value.dtype={value.dtype}"
        )
    # Mark symbols in custom kernel options as static shapes and add guards.
    kernel_options = {
        k: V.graph.sizevars.guard_int(v) if isinstance(v, sympy.Symbol) else v
        for k, v in kernel_options.items()
    }
    kernel_options.setdefault("FLOAT32_PRECISION", get_float32_precision())
    kernel_options.setdefault("PRESCALE_QK", False)
    kernel_options.setdefault("ROWS_GUARANTEED_SAFE", False)
    kernel_options.setdefault("BLOCKS_ARE_CONTIGUOUS", False)
    kernel_options.setdefault("WRITE_DQ", True)
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

    fwd_placeholder_inps = [
        create_placeholder(name, dtype, device)
        for name, dtype in [
            ("score", dtype),
            ("b", torch.int32),
            ("h", torch.int32),
            ("m", torch.int32),
            ("n", torch.int32),
        ]
    ]
    fw_subgraph_buffer = build_subgraph_buffer(
        fwd_placeholder_inps + list(score_mod_other_buffers), fw_graph
    )
    freeze_irnodes(fw_subgraph_buffer)

    joint_placeholder_inps = fwd_placeholder_inps + [
        create_placeholder("grad_score_mod", dtype, device)
    ]
    # Sometimes we have weird unused nodes here
    joint_graph.graph_module.graph.eliminate_dead_code()

    # It is hard to raise nice errors for some joint graphs during subgraph lowering
    # This lets us do some checks before attempting to lower
    validate_joint_graph(joint_graph.graph_module.graph)

    all_joint_outputs = build_subgraph_buffer(
        joint_placeholder_inps + list(score_mod_other_buffers),
        joint_graph,
    )

    freeze_irnodes(all_joint_outputs)

    joint_outputs = process_joint_outputs(
        all_joint_outputs, len(joint_placeholder_inps)
    )

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

    if _use_flex_flash_attention_backward(
        fw_graph,
        mask_graph,
        backend=backend,
        joint_outputs=joint_outputs,
        score_mod_other_buffers=score_mod_other_buffers,
    ):
        needs_block_mask = not is_trivial_mask_graph(mask_graph.graph_module)
        if (
            torch.are_deterministic_algorithms_enabled()
            and not torch.is_deterministic_algorithms_warn_only_enabled()
            and needs_block_mask
        ):
            raise NotImplementedError(
                "Deterministic backward for flex_attention with block_mask using the FLASH backend "
                "is not yet implemented. The TRITON backend supports deterministic backward."
            )
        if torch.is_deterministic_algorithms_warn_only_enabled() and needs_block_mask:
            warnings.warn(
                "Deterministic backward for flex_attention with block_mask using the FLASH backend "
                "is not yet implemented. Running non-deterministic backward.",
            )
        # TODO: Implement dLSE support in flash-attention backward by folding
        # grad_logsumexp into the dPsum preprocess step.
        if grad_logsumexp is not None:
            raise NotImplementedError(
                "FLASH backend backward does not support differentiating through "
                "logsumexp (dLSE). This happens when the loss depends on the LSE "
                "output of flex_attention. "
                "Use BACKEND='TRITON' or avoid differentiating through logsumexp."
            )
        score_is_trivial = is_trivial_score_graph(fw_graph.graph_module)
        return create_flex_flash_attention_backward_kernel(
            query,
            key,
            value,
            out,
            logsumexp,
            grad_out,
            scale,
            kernel_options,
            SPARSE_Q_BLOCK_SIZE,
            SPARSE_KV_BLOCK_SIZE,
            fw_subgraph_buffer=None if score_is_trivial else fw_subgraph_buffer,
            joint_subgraph_buffer=None
            if score_is_trivial
            else joint_outputs.grad_input,
            score_mod_other_buffers=list(score_mod_other_buffers),
            mask_graph_buffer=mask_graph_buffer if needs_block_mask else None,
            q_num_blocks=q_num_blocks if needs_block_mask else None,
            q_indices=q_indices if needs_block_mask else None,
            full_q_num_blocks=full_q_num_blocks if needs_block_mask else None,
            full_q_indices=full_q_indices if needs_block_mask else None,
        )

    # Construct layout with stride order matching K
    key_size = [Bq, Hkv, seq_len_kv, qk_head_dim]
    key_strides = infer_dense_strides(key_size, key.get_stride())

    layout_broadcasted_k = FixedLayout(
        key.get_device(),
        key.get_dtype(),
        key_size,
        stride=[sympy.sympify(s) for s in key_strides],
    )

    # Create delta which will is needed for the bwd's kernel
    mul_delta = lowerings[aten.mul](out, grad_out)
    delta = lowerings[aten.sum](mul_delta, axis=-1)
    delta = lowerings[prims.convert_element_type](delta, torch.float32)
    if grad_logsumexp is not None:
        grad_lse_exp2 = lowerings[aten.mul](grad_logsumexp, 1 / math.log(2))
        grad_lse_exp2 = ExternKernel.require_contiguous(grad_lse_exp2)
        delta = lowerings[aten.sub](delta, grad_lse_exp2)
        delta = ExternKernel.require_contiguous(delta)
        delta, grad_lse_exp2 = maybe_realize([delta, grad_lse_exp2])
    else:
        delta = ExternKernel.require_contiguous(delta)
        (delta,) = maybe_realize([delta])

    # # see NOTE:[TritonTemplates with multiple outputs]
    query_size = [Bq, Hq, seq_len_q, qk_head_dim]
    grad_query_strides = infer_dense_strides(query_size, query.get_stride())
    grad_query = empty_strided(
        query_size,
        stride=[sympy.sympify(s) for s in grad_query_strides],
        dtype=query.get_dtype(),
        device=query.get_device(),
    )

    # Construct output layout with stride order matching value
    value_size = [Bq, Hkv, seq_len_kv, v_head_dim]
    value_strides = infer_dense_strides(value_size, value.get_stride())

    broadcasted_grad_value = empty_strided(
        value_size,
        stride=[sympy.sympify(s) for s in value_strides],
        dtype=value.get_dtype(),
        device=value.get_device(),
    )

    kernel_options.setdefault("SM_SCALE", scale)

    # Determine GQA factor
    gqa_shared_heads = FloorDiv(Hq, Hkv)
    kernel_options.setdefault("GQA_SHARED_HEADS", gqa_shared_heads)

    # Inside of Triton kernel, only apply partial masking if partial blocks are computed.
    # full_kv_num_blocks is torch.zeros([1, 1, 1]) if partial blocks are not computed.
    has_full_blocks = full_kv_num_blocks is not None
    kernel_options.setdefault("HAS_FULL_BLOCKS", has_full_blocks)
    if not has_full_blocks:
        full_kv_num_blocks, full_kv_indices, full_q_num_blocks, full_q_indices = (
            empty(0, device=query.get_device()) for _ in range(4)
        )

    set_head_dim_values(kernel_options, qk_head_dim, v_head_dim, V.graph.sizevars)

    SPARSE_Q_BLOCK_SIZE = V.graph.sizevars.guard_int(SPARSE_Q_BLOCK_SIZE)
    SPARSE_KV_BLOCK_SIZE = V.graph.sizevars.guard_int(SPARSE_KV_BLOCK_SIZE)

    choices: list[Any] = []

    dtype = query.get_dtype()
    head_dim = V.graph.sizevars.guard_int(query.get_size()[-1])
    configs: list[FlexBwDConfig] = V.choices.get_flex_attention_bwd_configs(
        head_dim, dtype, query.get_device().type
    )

    # Default config for warp specialization
    num_consumer_groups, num_buffers_warp_spec = 0, 0

    original_kernel_options = kernel_options.copy()

    for conf in configs:
        if (
            SPARSE_KV_BLOCK_SIZE % conf.block_n1 != 0
            or SPARSE_Q_BLOCK_SIZE % conf.block_m1 != 0
            or SPARSE_KV_BLOCK_SIZE % conf.block_n2 != 0
            or SPARSE_Q_BLOCK_SIZE % conf.block_m2 != 0
        ):
            continue

        # Performance tuning
        # Triton heuristics
        cur_kernel_options = original_kernel_options.copy()
        # Remove prefix for backward kernels options and delete forward kernel options.
        for k in list(cur_kernel_options.keys()):
            if k.startswith("bwd_"):
                v = cur_kernel_options.pop(k)
                cur_kernel_options[k[4:]] = v
            if k.startswith("fwd_"):
                cur_kernel_options.pop(k)
        cur_kernel_options.setdefault("num_warps", conf.num_warps)
        cur_kernel_options.setdefault("num_stages", conf.num_stages)

        if cur_kernel_options.get("num_consumer_groups", False):
            cur_kernel_options.setdefault("num_consumer_groups", num_consumer_groups)
            cur_kernel_options.setdefault(
                "num_buffers_warp_spec", num_buffers_warp_spec
            )

        # Intel GPU enables TMA by default
        cur_kernel_options.setdefault("USE_TMA", bool(torch.xpu.is_available()))

        if cur_kernel_options["USE_TMA"] and not can_use_tma(query, key, value):
            cur_kernel_options["USE_TMA"] = False

        cur_kernel_options.setdefault("BLOCK_M1", conf.block_m1)
        cur_kernel_options.setdefault("BLOCK_N1", conf.block_n1)
        cur_kernel_options.setdefault("BLOCK_M2", conf.block_m2)
        cur_kernel_options.setdefault("BLOCK_N2", conf.block_n2)

        # Blocksparse options
        cur_kernel_options.setdefault("SPARSE_Q_BLOCK_SIZE", SPARSE_Q_BLOCK_SIZE)
        cur_kernel_options.setdefault("SPARSE_KV_BLOCK_SIZE", SPARSE_KV_BLOCK_SIZE)

        # ROCm specific kernargs
        for attrib in ["kpack", "matrix_instr_nonkdim", "waves_per_eu"]:
            if hasattr(conf, attrib):
                cur_kernel_options[attrib] = getattr(conf, attrib)

        flex_attention_backward_template.maybe_append_choice(
            choices=choices,
            input_nodes=[
                query,
                key,
                value,
                logsumexp,
                delta,
                grad_out,
                grad_query,
                broadcasted_grad_value,
                kv_num_blocks,
                kv_indices,
                q_num_blocks,
                q_indices,
                full_kv_num_blocks,
                full_kv_indices,
                full_q_num_blocks,
                full_q_indices,
            ],
            layout=layout_broadcasted_k,  # We use store_output only for grad_key
            subgraphs=[
                fw_subgraph_buffer,
                joint_outputs.grad_input,
                mask_graph_buffer,
                joint_outputs.captured_grads_compute,
            ],
            mutated_inputs=[
                grad_query,
                broadcasted_grad_value,
                *joint_outputs.mutated_grads,
            ],
            call_sizes=query.get_size() + key.get_size()[1:3],
            **cur_kernel_options,
        )
    inputs_for_autotuning = (
        [
            query,
            key,
            value,
            logsumexp,
            delta,
            grad_out,
            grad_query,
            broadcasted_grad_value,
            kv_num_blocks,
            kv_indices,
            q_num_blocks,
            q_indices,
            full_kv_num_blocks,
            full_kv_indices,
            full_q_num_blocks,
            full_q_indices,
        ]
        + list(score_mod_other_buffers)
        + list(mask_mod_other_buffers)
        + joint_outputs.mutated_grads
    )
    input_gen_fns = {
        8: create_num_blocks_fake_generator(kv_indices),  # kv_num_blocks
        9: create_indices_fake,
        10: create_num_blocks_fake_generator(q_indices),  # q_num_blocks
        11: create_indices_fake,
        12: create_num_blocks_fake_generator(full_kv_indices),  # full_kv_num_blocks
        13: create_indices_fake,
        14: create_num_blocks_fake_generator(full_q_indices),  # full_q_num_blocks
        15: create_indices_fake,
    }

    broadcasted_grad_key, _ = autotune_select_algorithm(
        "flex_attention_backward",
        choices,
        [x for x in inputs_for_autotuning if isinstance(x, torch._inductor.ir.IRNode)],
        layout_broadcasted_k,
        input_gen_fns=input_gen_fns,
    )  # [Bq, Hkv, seq_len_kv, k_head_dim]

    # need subgraph inputs and outputs to analyze all symints used in flex attention
    broadcasted_grad_key.data.data.subgraph_inps = list(score_mod_other_buffers) + list(
        mask_mod_other_buffers
    )
    broadcasted_grad_key.data.data.subgraph_outs = get_bwd_subgraph_outputs(
        fw_subgraph_buffer, mask_graph_buffer, joint_outputs
    )

    if V.graph.sizevars.evaluate_expr(sympy.Eq(Bq, Bkv)):
        grad_key = broadcasted_grad_key
        grad_value = broadcasted_grad_value
    else:
        assert V.graph.sizevars.evaluate_expr(sympy.Gt(Bq, 1) & sympy.Eq(Bkv, 1)), (
            f"Bq and Bkv must broadcastable. "
            f"Got Bq={V.graph.sizevars.evaluate_expr(Bq)} "
            f"and Bkv={V.graph.sizevars.evaluate_expr(Bkv)}"
        )
        grad_key = lowerings[aten.sum](broadcasted_grad_key, axis=0, keepdims=True)
        grad_value = lowerings[aten.sum](broadcasted_grad_value, axis=0, keepdims=True)

    # Cast captured grads to match original buffer dtypes. Gradients are accumulated
    # in fp32 for precision, then cast to the original dtype (e.g., bf16) here.
    captured_grads = tuple(
        to_dtype(g, orig.get_dtype())
        if g is not None and g.get_dtype() != orig.get_dtype()
        else g
        for g, orig in zip(joint_outputs.captured_grads, score_mod_other_buffers)
    )

    return (grad_query, grad_key, grad_value, captured_grads)
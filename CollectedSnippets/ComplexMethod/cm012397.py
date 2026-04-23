def create_flex_flash_attention_kernel(
    query: TensorBox,
    key: TensorBox,
    value: TensorBox,
    block_mask: tuple[Any, ...],
    scale: float,
    kernel_options: dict[str, Any],
    subgraph_buffer: SubgraphResults,
    mask_graph_buffer: SubgraphResults,
    score_mod_other_buffers: list[TensorBox],
    mask_mod_other_buffers: list[TensorBox],
    kv_num_blocks: TensorBox | None,
    kv_indices: TensorBox | None,
    full_kv_num_blocks: TensorBox | None,
    full_kv_indices: TensorBox | None,
    sparse_q_block_size: int,
    sparse_kv_block_size: int,
    mask_graph: Subgraph,
    subgraph: Subgraph | None = None,
) -> tuple[TensorBox, TensorBox]:
    """Create a flex flash attention kernel using CuteDSL template."""
    if query.dtype != key.dtype or query.dtype != value.dtype:
        raise ValueError(
            f"Mixed query, key, and value dtype is not supported on this platform, "
            f"got query.dtype: {query.dtype}, key.dtype: {key.dtype}, "
            f"and value.dtype: {value.dtype}."
        )
    if not ensure_flash_available():
        raise RuntimeError("CUTE flash attention not available")

    # Get dimensions
    batch_size, num_heads, seq_len_q, head_dim = query.get_size()
    v_head_dim = value.get_size()[-1]
    device = query.get_device()
    dtype = query.get_dtype()
    assert device is not None, "Device must be specified"

    # Match stride pattern from query tensor
    q_strides = query.get_stride()
    out_size = [batch_size, num_heads, seq_len_q, v_head_dim]
    out_strides = infer_dense_strides(out_size, q_strides)

    output = empty_strided(
        size=out_size,
        stride=out_strides,
        dtype=dtype,
        device=device,
    )

    lse = empty_strided(
        size=[batch_size, num_heads, seq_len_q],
        stride=None,  # LSE can be contiguous
        dtype=torch.float32,  # LSE is always fp32
        device=device,
    )

    # Create layout for primary output
    output_layout = FixedLayout(
        device=device,
        dtype=dtype,
        size=[batch_size, num_heads, seq_len_q, v_head_dim],
        stride=[sympy.sympify(s) for s in output.get_stride()],
    )

    sparse_q_block_size = V.graph.sizevars.guard_int(sparse_q_block_size)
    sparse_kv_block_size = V.graph.sizevars.guard_int(sparse_kv_block_size)

    mask_graph_is_trivial = is_trivial_mask_graph(mask_graph.graph_module)
    score_graph_is_trivial = subgraph is None or is_trivial_score_graph(
        subgraph.graph_module
    )

    needs_block_mask = not mask_graph_is_trivial
    has_score_mod = not score_graph_is_trivial
    has_full_blocks = full_kv_num_blocks is not None

    choices: list[Any] = []
    assert flash_attention_cutedsl_template is not None

    input_nodes = [query, key, value, lse]
    if has_full_blocks:
        input_nodes.extend(
            [kv_num_blocks, kv_indices, full_kv_num_blocks, full_kv_indices]
        )

    if needs_block_mask and not has_full_blocks:
        raise NotImplementedError(
            "Flash attention with block mask but without full blocks is not supported yet"
        )

    subgraphs = []
    if has_score_mod:
        subgraphs.append(subgraph_buffer)
    subgraphs.append(mask_graph_buffer)

    configs = _get_flex_flash_fwd_configs(
        has_score_mod, len(score_mod_other_buffers) > 0
    )

    error: NotImplementedError | None = None
    for conf in configs:
        with patch_fixed_layout_indexer_for_cutedsl():
            error = flash_attention_cutedsl_template.maybe_append_choice(
                choices,
                input_nodes=input_nodes,
                layout=output_layout,
                mutated_inputs=[lse],
                subgraphs=subgraphs,
                SM_SCALE=scale,
                HAS_SCORE_MOD=has_score_mod,
                SCORE_MOD_VEC_SIZE=conf.score_mod_vec_size,
                NEEDS_BLOCK_MASK=needs_block_mask,
                SPARSE_Q_BLOCK_SIZE=sparse_q_block_size,
                SPARSE_KV_BLOCK_SIZE=sparse_kv_block_size,
            )
        if error is not None and len(configs) == 1:
            raise RuntimeError(f"CuteDSL template failed: {error}")

    for choice in choices:
        wrap_choice_render_with_cutedsl_indexer(choice)

    if not choices:
        raise RuntimeError(f"CuteDSL template failed: {error}")

    input_gen_fns: dict[int, Callable] | None = None
    if has_full_blocks:
        input_gen_fns = {
            4: create_num_blocks_fake_generator(kv_indices),
            5: create_indices_fake,
            6: create_num_blocks_fake_generator(full_kv_indices),
            7: create_indices_fake,
        }

    template_output, _ = autotune_select_algorithm(
        "flex_flash_attention",
        choices,
        input_nodes,
        output_layout,
        input_gen_fns=input_gen_fns,
        return_multi_template=False,
    )

    return (template_output, lse)
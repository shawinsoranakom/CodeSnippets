def _aot_export_function(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    *,
    num_params_buffers: int = 0,
    decompositions: dict[OpOverload, Callable[..., Any]] | None = None,
    # If we're exporting a joint graph and we don't want any tangent inputs in the graph
    # (because we are backpropping through a scalar 1 loss),
    # we need to explicitly specify not to include tangents in the graph.
    # It's not enough just to check that our tangent is a scalar, since we also
    # need to know if it is a 1 (no need to make it a graph input), or something else
    # (requiring it to be a graph input).
    # We don't know this info at trace time though, so we need to make it an explicit config.
    no_tangents: bool = False,
    pre_dispatch: bool = False,
    # If None, `dynamic_shapes` will be inferred from inputs, but the inferred result might be wrong.
    dynamic_shapes: bool | None = None,
    keep_input_mutations: bool = False,
    # Under export, configures whether we are getting inference or training IR
    trace_joint: bool = False,
    kwargs: dict[str, Any] | None = None,
) -> tuple[
    Callable[..., Any], ViewAndMutationMeta, pytree.TreeSpec, pytree.TreeSpec | None
]:
    kwargs = kwargs or {}

    flat_fn, out_spec = create_tree_flattened_fn(func, args, kwargs)
    flat_args, in_spec = pytree.tree_flatten((args, kwargs))

    fake_mode = None
    if dynamic_shapes is None:
        # Try to infer `dynamic_shapes from inputs and graph nodes
        fake_mode = detect_fake_mode(flat_args)
        if (
            fake_mode is None
            and hasattr(func, "_orig_mod")
            and isinstance(func._orig_mod, torch.fx.GraphModule)
        ):
            vals = [
                node.meta["val"]
                for node in func._orig_mod.graph.nodes
                if "val" in node.meta
            ]
            fake_mode = detect_fake_mode(vals)
        dynamic_shapes = fake_mode is not None and fake_mode.shape_env is not None

    # The export use case doesn't care about several bits of AOTConfig
    # (1) compilers (we just export the graph)
    # (2) partitioners (export is only full graph, user can partition themselves)
    aot_config = AOTConfig(  # type: ignore[arg-type]
        fw_compiler=None,
        bw_compiler=None,
        inference_compiler=None,
        partition_fn=None,
        decompositions=decompositions,
        num_params_buffers=num_params_buffers,
        aot_id=next(AOT_COUNTER),
        keep_inference_input_mutations=keep_input_mutations,
        dynamic_shapes=dynamic_shapes,
        aot_autograd_arg_pos_to_source=None,
        is_export=True,
        no_tangents=no_tangents,
        pre_dispatch=pre_dispatch,
        export_trace_joint=trace_joint,
    )
    if fake_mode is None:
        fake_mode, shape_env = construct_fake_mode(flat_args, aot_config)
    else:
        shape_env = fake_mode.shape_env
    fake_flat_args, act_input_indices = process_inputs(
        flat_args, aot_config, fake_mode, shape_env
    )
    # TODO: Improve the descs here with pytree information
    fake_flat_args_descs: list[AOTInput] = [
        PlainAOTInput(i) for i in range(len(fake_flat_args))
    ]

    with contextlib.ExitStack() as stack:
        aot_state = create_aot_state(
            stack,
            flat_fn,
            fake_flat_args,
            fake_flat_args_descs,
            aot_config,
            fake_mode,
            shape_env,
        )
        aot_state.fw_metadata.act_input_indices = act_input_indices
        aot_graph_capture = aot_stage1_graph_capture(aot_state, flat_fn)
        fx_g, meta = aot_stage2_export(aot_state, aot_graph_capture)

    return fx_g, meta, in_spec, out_spec.spec
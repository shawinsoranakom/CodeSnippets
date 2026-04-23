def autograd_cache_key(
    graph,
    example_inputs,
    ignore_shape_env: bool,
    decompositions=None,
):
    if config.cpp_wrapper or config.fx_wrapper:
        raise RuntimeError(
            "autograd_cache_key is not supported with cpp_wrapper or fx_wrapper"
        )

    decompositions = (
        decompositions if decompositions is not None else select_decomp_table()
    )
    # compile_fx applies these graph transforms before reaching _compile_fx_main.
    # Neither occurs on the torch.compile/Dynamo path (which always produces
    # tuple-returning, pre-flattened graphs). Not supported by this API.
    if isinstance(graph, GraphModule) and not graph_returns_tuple(graph):
        raise NotImplementedError(
            "autograd_cache_key does not support graphs that don't return a tuple"
        )
    if any(isinstance(x, (list, tuple, dict)) for x in example_inputs):
        raise NotImplementedError(
            "autograd_cache_key does not support nested container inputs"
        )

    compiler_config_extra = create_compiler_config_extra(graph)

    # These context managers replicate the ones that _compile_fx_main sets up
    # before calling aot_autograd, so that the config snapshot captured by
    # autograd_cache_key is identical to a real compile_fx run:
    #   _compile_fx_main outer with-block: _use_lazy_graph_module,
    #       enable_python_dispatcher, preserve_node_meta,
    #       reset_provenance_globals
    #   _compile_fx_main aot_autograd with-block: V.set_fake_mode,
    #       torch._guards.tracing, compiled_autograd._disable,
    #       functorch_config.patch

    fake_mode = detect_fake_mode(example_inputs) or torch._subclasses.FakeTensorMode(
        allow_non_fake_inputs=True
    )
    tracing_context = (
        torch._guards.TracingContext.try_get()
        or torch._guards.TracingContext(fake_mode)
    )

    with (
        functorch_config.patch(
            unlift_effect_tokens=True, selective_decompose=config.selective_decompose
        ),
        _use_lazy_graph_module(dynamo_config.use_lazy_graph_module),
        enable_python_dispatcher(),
        torch.fx.traceback.preserve_node_meta(
            config.trace.provenance_tracking_level == 1
        ),
        torch._inductor.debug.reset_provenance_globals(),
        V.set_fake_mode(fake_mode),
        torch._guards.tracing(tracing_context),
        compiled_autograd._disable(),
    ):
        return aot_autograd.autograd_cache_key(
            graph,
            example_inputs,
            ignore_shape_env=ignore_shape_env,
            decompositions=decompositions,
            compiler_config_extra=compiler_config_extra,
            keep_inference_input_mutations=True,
        )
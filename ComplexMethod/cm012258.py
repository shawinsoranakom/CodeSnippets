def joint_graph_passes(
    graph: torch.fx.GraphModule,
    input_device: torch.device | None = None,
):
    """
    Run FX transformations on the joint forwards+backwards graph.
    """
    GraphTransformObserver = functools.partial(
        torch.fx.passes.graph_transform_observer.GraphTransformObserver,
        subsystem="joint_graph_passes",
    )

    lazy_init(input_device)
    count = 0

    # must occur before other passes
    canonicalize_aten_ir_passes(graph)

    if config.joint_custom_pre_pass is not None:
        GraphTransformObserver(graph, "joint_custom_pre_pass").apply_graph_pass(
            config.joint_custom_pre_pass
        )
        count += 1

    from .post_grad import remove_noop_ops

    GraphTransformObserver(graph, "remove_noop_ops").apply_graph_pass(remove_noop_ops)

    if config.joint_graph_constant_folding:
        GraphTransformObserver(graph, "constant_fold_uniform_value").apply_gm_pass(
            constant_fold_uniform_value
        )

    if config.pattern_matcher:
        count += early_patterns.apply(graph.graph)

    # Make sure AutoChunker happens before pad_mm so we don't need
    # to handle padding when searching for chunking patterns.
    if config.auto_chunker.enable:
        from .auto_chunker import CantChunk, chunk

        try:
            graph = chunk(graph)
        except CantChunk:
            auto_chunker_log = torch._logging.getArtifactLogger(
                __name__, "auto_chunker"
            )
            auto_chunker_log.debug("AutoChunker fail.", exc_info=True)

    if config.pattern_matcher:
        for i, patterns in enumerate(pass_patterns):
            maybe_count = GraphTransformObserver(
                graph, f"pass_pattern_{i}"
            ).apply_graph_pass(patterns.apply)
            count += maybe_count if maybe_count is not None else 0

    if not config.fallback_random:
        # not trying into the bisector because decomps may have already affected rng reproducibility
        # we'll instead explicitly turn off the config
        count += replace_random_passes(graph)

    if config.joint_custom_post_pass is not None:
        GraphTransformObserver(graph, "joint_custom_post_pass").apply_graph_pass(
            config.joint_custom_post_pass
        )
        count += 1

    if count:
        stable_topological_sort(graph.graph)
        graph.graph.lint()
        graph.recompile()
    return graph
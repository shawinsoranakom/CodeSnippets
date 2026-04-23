def check_cacheable(gm: torch.fx.GraphModule) -> None:
    """
    Checks that the graph module only uses supported operators
    """
    nodes = gm.graph.nodes
    if torch._inductor.config.freezing:
        raise BypassAOTAutogradCache("Cannot cache a graph with freezing enabled")

    if not (
        torch._inductor.config.fx_graph_cache or should_use_remote_fx_graph_cache()
    ):
        raise BypassAOTAutogradCache("FX graph cache is not enabled")

    tracing_context = torch._guards.TracingContext.try_get()
    if tracing_context and tracing_context.fakify_first_call:
        raise BypassAOTAutogradCache(
            "Won't cache a graph with fakify_first_call enabled"
        )
    for node in nodes:
        check_node_safe(node)

    # Saved tensors hooks are globally set subgraphs,
    # that are not used explicitly in the main graph.
    # They are inlined in aot_autograd graphs.
    # Subgraphs are only used for caching logic.
    if hasattr(gm, "saved_tensors_hooks_pack_0"):
        check_cacheable(gm.saved_tensors_hooks_pack_0)  # type: ignore[arg-type]
        # We have guarantee of unpack sugraph existence if pack subgraph exists
        check_cacheable(gm.saved_tensors_hooks_unpack_0)
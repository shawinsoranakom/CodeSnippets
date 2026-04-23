def is_with_effects(node: torch.fx.Node) -> bool:
    if (
        node.op == "call_function"
        and node.target is torch.ops.higher_order.with_effects
    ):
        return True
    elif (
        node.op == "call_function"
        and node.target is torch.ops.higher_order.invoke_subgraph
    ):
        # Check if subgraph has effects by looking in the cache
        from torch._guards import InvokeSubgraphCache, TracingContext

        tracing_ctx = TracingContext.try_get()
        if tracing_ctx:
            invoke_subgraph_cache = tracing_ctx.hop_dispatch_set_cache.get_cache(
                torch.ops.higher_order.invoke_subgraph
            )
            if invoke_subgraph_cache:
                if not isinstance(invoke_subgraph_cache, InvokeSubgraphCache):
                    raise AssertionError(
                        f"expected InvokeSubgraphCache, got {type(invoke_subgraph_cache)}"
                    )
                # pyrefly: ignore[bad-argument-type]
                effects = invoke_subgraph_cache.get_effects(node.args[1])
                return effects is not None
    return False
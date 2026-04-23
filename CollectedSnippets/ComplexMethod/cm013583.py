def _compile_submod(
    gm: torch.fx.GraphModule, subgraph: str, subgraph_users: list[torch.fx.Node]
) -> torch.fx.GraphModule:
    """
    Compiles subgraph submodule in gm. subgraph is used by subgraph_users.
    subgraph_users must all be  torch.ops.higher_order.invoke_subgraph HOP.
    """

    submod = getattr(gm, subgraph)

    compile_config = None
    fake_inputs = []

    # We use the first user for compile configs and inputs
    sub_node = subgraph_users[0]
    if not _needs_inductor_compile(sub_node):
        raise AssertionError("sub_node does not need inductor compile")
    compile_config = sub_node.meta["custom"]["nested_region_config"]
    if sub_node.meta.get("partitioner_tag") == "is_forward":
        compile_fn = compile_config.fw_compiler
    else:
        compile_fn = compile_config.bw_compiler

    for inp_node in sub_node.all_input_nodes[
        1:
    ]:  # exlucde the graph module input to torch.ops.higher_order.invoke_subgraph
        if hasattr(inp_node, "meta") and "val" in inp_node.meta:
            fake_inputs.append(inp_node.meta["val"])
        else:
            raise RuntimeError(
                f"Partition is bad because non fake tensor value is seen {inp_node}"
            )

    # Log the options being used
    logger.info(
        "Compiling submodule %s with inductor options: %s",
        subgraph,
        compile_config,
    )

    def get_compiled_fn() -> AOTCompiledArtifact:
        context = torch._guards.TracingContext.get()
        if context.fake_mode is None:
            raise AssertionError("context.fake_mode is None")

        context = torch._guards.TracingContext(context.fake_mode)

        with (
            torch._guards.tracing(context),
            CacheArtifactManager.with_fresh_cache(),
            torch._functorch.config.patch("bundled_autograd_cache", True),
            _disable_remat_for_regional_subcompile(),
        ):
            # compile_fx can mutate gm
            gm = copy.deepcopy(submod)

            compiled_fn = compile_fn(gm, fake_inputs)
            return compiled_fn

    compiled_fn = get_compiled_fn()
    if not isinstance(compiled_fn, AOTCompiledArtifact):
        raise AssertionError(f"Expected AOTCompiledArtifact, got {type(compiled_fn)}")

    # _dummy_wrapper is to make call_function happy
    compiled_submod = _dummy_wrapper(compiled_fn)
    for node in subgraph_users:
        with gm.graph.inserting_after(node):
            new_node = gm.graph.call_function(
                # exclude graph nodes input args
                compiled_submod,
                args=node.args[2:],
                kwargs=node.kwargs,
            )
            new_node.meta = node.meta
            node.replace_all_uses_with(new_node)
            gm.graph.erase_node(node)

    gm.recompile()
    return gm
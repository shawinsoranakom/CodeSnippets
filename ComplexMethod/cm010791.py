def remat_using_tags_for_fwd_loss_bwd_graph(gm: fx.GraphModule) -> fx.GraphModule:
    """
    Duplicate recompute nodes for backward use. DCE removes unused forward versions.

    Backward regions are identified by custom["phase"] == "backward" (user
    annotation) or node.meta["autograd_backward"] == True (set automatically when
    Dynamo traces torch.autograd.grad). When the user provides phase
    annotations, only those annotated regions are used.

    The graph may contain multiple disjoint backward regions (e.g. chunked
    loss). Regions that do not depend on recomputable forward nodes are
    skipped. Only one region may require remat; if multiple do, we error
    and ask the user to annotate which region to rematerialize.
    """
    if not has_recomputable_ops(gm):
        return gm

    if has_recomputable_rng_ops(gm):
        raise RuntimeError(
            "Activation checkpoint rematerialization in `forward-loss-backward` graph does not support RNG ops "
            "in recompute regions. Please move RNG operations outside "
            "of recompute regions, or use joint graph mode (where partitioner handles RNG)."
        )

    # Use partitioner pass to normalize AC node tags.
    gm = cleanup_recompute_tags(gm, is_default_partition=True)

    force_save_bw_mutation_src(gm)

    # must_recompute (used inside _collect_backward_regions) requires
    # cleanup_recompute_tags to have run first.
    use_phase = _has_user_phase_annotation(gm)
    regions = _collect_backward_regions(gm, use_phase)
    if not regions:
        return gm

    # User-annotated phase regions: multiple annotations is always an error.
    if use_phase and len(regions) > 1:
        raise RuntimeError(
            f"Detected {len(regions)} disjoint backward regions annotated with "
            'phase: "backward" but remat only supports a single backward region. '
            "Please ensure only one contiguous region is annotated."
        )

    remat_regions = [(s, e) for s, e, needs in regions if needs]

    if len(remat_regions) > 1:
        raise RuntimeError(
            f"Detected {len(remat_regions)} disjoint backward regions that require recomputation, "
            "but remat only supports one such region in a forward-loss-backward graph."
        )

    if not remat_regions:
        return gm

    bwd_start, bwd_end = remat_regions[0]

    order = {node: idx for idx, node in enumerate(gm.graph.nodes)}
    new_graph = fx.Graph()
    env: dict[fx.Node, fx.Node] = {}
    recomputed_nodes: dict[fx.Node, fx.Node] = {}

    # Insert forward nodes
    for node in itertools.islice(gm.graph.nodes, 0, bwd_start):
        env[node] = new_graph.node_copy(node, lambda x: env[x])

    @overload
    def remat_input(x: fx.Node) -> fx.Node: ...
    @overload
    def remat_input(x: Any) -> Any: ...

    def remat_input(x: object) -> object:
        # fx.Node can have args that are primitive types (e.g. int, float, bool)
        if not isinstance(x, fx.Node):
            return x
        return recomputed_nodes.get(x, env[x])

    def gather_recompute_deps(node: fx.Node) -> set[fx.Node]:
        deps: set[fx.Node] = set()

        def _gather(n: fx.Node) -> None:
            if n in deps or n in recomputed_nodes or not must_recompute(n):
                return
            deps.add(n)
            for inp in n.all_input_nodes:
                _gather(inp)

        # Can't call _gather(node) directly: node itself may not be must_recompute
        # (e.g. backward nodes), so _gather would return early without visiting inputs.
        for inp in node.all_input_nodes:
            _gather(inp)
        return deps

    # Insert backward nodes
    for node in itertools.islice(gm.graph.nodes, bwd_start, bwd_end):
        # Gather all deps that need to be recomputed for this node
        deps = gather_recompute_deps(node)

        # Insert deps in forward order (guaranteed disjoint from already-inserted)
        # This is not as inefficient as it looks, because we only add fresh dependencies
        # when they are not yet processed as recomputed nodes.
        new_deps = sorted(deps, key=lambda n: order[n])
        if new_deps:
            log.debug(
                "To compute backward node %s, recomputing [%s]",
                node.name,
                ", ".join(dep.name for dep in new_deps),
            )
        for dep in new_deps:
            dup = new_graph.node_copy(dep, remat_input)
            dup.name = dep.name + "_recomputed"
            recomputed_nodes[dep] = dup

        env[node] = new_graph.node_copy(node, remat_input)

    for node in itertools.islice(gm.graph.nodes, bwd_end, None):
        env[node] = new_graph.node_copy(node, lambda x: env[x])

    new_gm = torch.fx.GraphModule(gm, new_graph)

    # DCE with custom is_impure_node (like default_partition)
    # Treats certain collectives as pure while delegating to default impurity logic
    new_gm.graph.eliminate_dead_code(is_impure_node=is_impure_node_for_dce)

    # raise_getitems pass for better memory (like default_partition)
    new_gm = raise_getitems(new_gm)

    new_gm.recompile()

    return new_gm
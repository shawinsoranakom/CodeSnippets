def min_cut_rematerialization_partition(
    joint_module: fx.GraphModule,
    _joint_inputs: Any,
    compiler: str = "inductor",
    *,
    num_fwd_outputs: int,
    static_lifetime_input_indices: list[int] | None = None,
) -> tuple[fx.GraphModule, fx.GraphModule]:
    """
    Partitions the joint graph such that the backward recomputes the forward.
    Recomputing helps in trading off memory bandwidth with computation.

    To create the fwd and bwd graph, we copy the joint graph, manually set the
    outputs to just original forward or backward outputs. And then we run the
    resulting graphs through dead code elimination.

    .. warning::
        This API is experimental and likely to change.

    Args:
        joint_module(fx.GraphModule): The joint forward and backward graph. This
            is the result of AOT Autograd tracing.
        _joint_inputs: The inputs to the joint graph. This is unused.
        compiler: This option determines the default set of recomputable ops.
            Currently, there are two options: ``nvfuser`` and ``inductor``.
        recomputable_ops: This is an optional set of recomputable ops. If this
            is not None, then this set of ops will be used instead of the
            default set of ops.
        num_fwd_outputs: The number of outputs from the forward graph.

    Returns:
        Returns the generated forward and backward Fx graph modules.
    """

    joint_module.graph.eliminate_dead_code()
    joint_module.recompile()

    fx_g = joint_module.graph

    #  add the CSE pass
    if config.cse:
        cse_graph = fx_graph_cse(fx_g)
        joint_module.graph = cse_graph
    joint_graph = joint_module.graph

    graph_has_recomputable_ops = has_recomputable_ops(joint_module)
    graph_has_recomputable_rng_ops = has_recomputable_rng_ops(joint_module)
    if graph_has_recomputable_ops:
        joint_module = cleanup_recompute_tags(joint_module, is_default_partition=False)
    if not config.unsafe_allow_optimization_of_collectives:
        force_save_collectives(joint_module)

    force_save_effectful_ops(joint_module)
    force_save_bw_mutation_src(joint_module)

    if static_lifetime_input_indices is None:
        static_lifetime_input_indices = []
    node_info = classify_nodes(
        joint_module, static_lifetime_input_indices, num_fwd_outputs
    )

    # networkx blows up on graphs with no required backward nodes
    # Since there's nothing to partition anyway, and the default partitioner can "handle"
    # this case, send our graph over to the default partitioner.
    if len(node_info.required_bw_nodes) == 0:
        return default_partition(
            joint_module,
            _joint_inputs,
            num_fwd_outputs=num_fwd_outputs,
            static_lifetime_input_indices=static_lifetime_input_indices,
            static_lifetime_input_nodes=node_info.static_lifetime_input_nodes,
        )

    for node in reversed(joint_module.graph.nodes):
        if node.op == "output":
            node.dist_from_bw = int(1e9)
        elif not node_info.is_required_fw(node):
            node.dist_from_bw = 0
        else:
            node.dist_from_bw = int(1e9)
            for user in node.users:
                node.dist_from_bw = min(node.dist_from_bw, user.dist_from_bw + 1)

    memory_budget = config.activation_memory_budget
    for node in joint_graph.nodes:
        if isinstance(node.meta.get("memory_budget", None), float):
            memory_budget = node.meta["memory_budget"]
            break
    saved_values = choose_saved_values_set(
        joint_graph,
        node_info,
        memory_budget=memory_budget,
    )
    # pyrefly: ignore [unbound-name]
    if config._sync_decision_cross_ranks:
        saved_values = _sync_decision_cross_ranks(joint_graph, saved_values)

    # save_for_backward on tensors and stashes symints in autograd .ctx
    # Skip SymBool nodes whose only consumers are _assert_scalar calls.
    # These are runtime assertion intermediates and are not needed in backward
    # for any real computation.
    def _is_assert_only_symbool(n: fx.Node) -> bool:
        return (
            isinstance(n.meta.get("val"), torch.SymBool)
            and len(n.users) > 0
            and all(u.target is torch.ops.aten._assert_scalar.default for u in n.users)
        )

    saved_sym_nodes = list(
        filter(
            lambda n: is_sym_node(n) and not _is_assert_only_symbool(n), saved_values
        )
    )
    saved_opaque_nodes = list(filter(is_opaque_node, saved_values))
    saved_values = list(
        filter(lambda n: not is_sym_node(n) and not is_opaque_node(n), saved_values)
    )

    # NB: saved_sym_nodes will be mutated to reflect the actual saved symbols
    fw_module, bw_module = _extract_fwd_bwd_modules(
        joint_module,
        saved_values,
        # pyrefly: ignore [bad-argument-type]
        saved_sym_nodes=saved_sym_nodes,
        saved_opaque_nodes=saved_opaque_nodes,
        num_fwd_outputs=num_fwd_outputs,
        static_lifetime_input_nodes=node_info.static_lifetime_input_nodes,
    )
    if graph_has_recomputable_ops:
        if graph_has_recomputable_rng_ops:
            fw_module, bw_module = functionalize_rng_ops(
                joint_module, fw_module, bw_module, len(saved_sym_nodes)
            )
    bw_module = reordering_to_mimic_autograd_engine(bw_module)

    # pyrefly: ignore [unbound-name]
    if config.enable_activation_offloading:
        from ._activation_offloading.activation_offloading import (
            enable_activation_offloading,
        )

        enable_activation_offloading(
            fw_module,
            bw_module,
            num_fwd_outputs,
            node_info.static_lifetime_input_nodes,
        )

    # raise all getitem ops to as early as possible
    # this is helpful for memory, especially in the case of aot_eager backend
    fw_module = raise_getitems(fw_module)
    bw_module = raise_getitems(bw_module)

    fw_module = thread_graphsafe_rng_from_hops(fw_module, is_backward=False)
    bw_module = thread_graphsafe_rng_from_hops(bw_module, is_backward=True)

    if AOT_PARTITIONER_DEBUG:
        # Calculate sorted sizes of saved values
        sorted_sizes = sorted([(_size_of(i), str(i)) for i in saved_values])

        # Log total theoretical activations stored
        total_activations_size_gb = sum(_size_of(i) for i in saved_values) / 1e9
        log.info("Theoretical Activations Stored: %.2f GB", total_activations_size_gb)

        # Log theoretical per activation storage sizes
        log.info("Theoretical Per Activation Storage Sizes: %s", sorted_sizes)
        fw_module_nodes = OrderedSet(
            node.name for node in fw_module.graph.nodes if node.op == "call_function"
        )
        bw_module_nodes = OrderedSet(
            node.name for node in bw_module.graph.nodes if node.op == "call_function"
        )
        remat_nodes = fw_module_nodes & bw_module_nodes

        counts: dict[str, int] = defaultdict(int)
        for node in fw_module.graph.nodes:
            if node.name in remat_nodes and hasattr(node.target, "_overloadpacket"):
                counts[str(node.target._overloadpacket)] += 1
        log.info(
            "# remat/fw/bw: %d/%d/%d",
            len(remat_nodes),
            len(fw_module_nodes),
            len(bw_module_nodes),
        )
        rematerialized_ops = sorted(
            counts.items(), key=operator.itemgetter(1), reverse=True
        )
        log.info("Count of Ops Rematerialized: %s", rematerialized_ops)
    return fw_module, bw_module
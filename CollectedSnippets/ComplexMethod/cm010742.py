def choose_saved_values_set(
    joint_graph: fx.Graph,
    node_info: NodeInfo,
    memory_budget: float = 1,
) -> list[fx.Node]:
    if memory_budget > 1 or memory_budget < 0:
        raise RuntimeError(
            f"The valid ranges for memory budget are 0 <= m <= 1. The provided value is {memory_budget}"
        )
    min_cut_options = MinCutOptions(
        ban_if_used_far_apart=config.ban_recompute_used_far_apart,
        ban_if_long_fusible_chains=config.ban_recompute_long_fusible_chains,
        ban_if_materialized_backward=config.ban_recompute_materialized_backward,
        ban_if_not_in_allowlist=config.ban_recompute_not_in_allowlist,
        ban_if_reduction=config.ban_recompute_reductions,
    )

    if config.aggressive_recomputation:
        min_cut_options = replace(
            min_cut_options,
            ban_if_used_far_apart=False,
            ban_if_long_fusible_chains=False,
            ban_if_materialized_backward=False,
            ban_if_not_in_allowlist=False,
        )
    if memory_budget == 0:
        return node_info.inputs

    runtime_optimized_saved_values, _ = solve_min_cut(
        joint_graph,
        node_info,
        min_cut_options,
    )
    # return runtime_optimized_saved_values
    if memory_budget == 1:
        return runtime_optimized_saved_values

    def estimate_activations_size(saved_values: list[fx.Node]) -> float:
        return sum(map(_size_of, saved_values)) / 1e9

    min_act_size = estimate_activations_size(node_info.inputs)
    max_act_size = estimate_activations_size(runtime_optimized_saved_values)
    # The optimized choice is smaller than the inputs anyways
    if max_act_size <= min_act_size:
        return runtime_optimized_saved_values

    def get_normalized_size(sz: float) -> float:
        return (sz / 1e9) / (max_act_size - min_act_size)

    def get_mem_ratio(activations: list[fx.Node]) -> float:
        return (estimate_activations_size(activations) - min_act_size) / (
            max_act_size - min_act_size
        )

    more_aggressive_options = replace(
        min_cut_options,
        ban_if_used_far_apart=False,
        ban_if_long_fusible_chains=False,
        ban_if_materialized_backward=False,
    )
    more_aggressive_saved_values, _ = solve_min_cut(
        joint_graph, node_info, more_aggressive_options
    )
    more_aggressive_saved_values_mem_ratio = get_mem_ratio(more_aggressive_saved_values)
    if more_aggressive_saved_values_mem_ratio < memory_budget:
        return more_aggressive_saved_values

    aggressive_options = replace(
        more_aggressive_options,
        ban_if_not_in_allowlist=False,
    )
    aggressive_recomputation_saved_values, banned_nodes = solve_min_cut(
        joint_graph, node_info, aggressive_options
    )

    aggressive_recomputation_saved_values_mem_ratio = get_mem_ratio(aggressive_recomputation_saved_values)
    if aggressive_recomputation_saved_values_mem_ratio < memory_budget:
        return aggressive_recomputation_saved_values

    from torch._inductor.fx_utils import get_node_storage

    input_storages = OrderedSet(get_node_storage(node) for node in node_info.inputs)

    def get_recomputable_banned_nodes(
        banned_nodes: OrderedSet[fx.Node],
    ) -> list[fx.Node]:
        return [
            i
            for i in banned_nodes
            if (
                # Only allow recomputing nodes that are actually required for BW
                i.dist_from_bw < int(1e9)  # type: ignore[attr-defined]
                and (
                    get_node_storage(i) not in input_storages
                    or is_non_builtin_to_include(i)
                )
            )
        ]

    recomputable_banned_nodes = get_recomputable_banned_nodes(banned_nodes)
    must_save_nodes = [
        i
        for i in recomputable_banned_nodes
        if i.meta.get("recompute", False) == CheckpointPolicy.MUST_SAVE
    ]
    recomputable_banned_nodes = [
        i for i in recomputable_banned_nodes if i not in must_save_nodes
    ]

    # default: runtime_optimized_saved_values
    # more aggressive: more_aggressive_saved_values
    # full aggressive: aggressive_recomputation_saved_values

    all_recomputable_banned_nodes = sorted(
        recomputable_banned_nodes, key=_size_of, reverse=True
    )
    if len(all_recomputable_banned_nodes) == 0:
        return node_info.inputs + must_save_nodes
    memories_banned_nodes = [
        get_normalized_size(_size_of(i)) for i in all_recomputable_banned_nodes
    ]
    runtimes_banned_nodes = [
        estimate_runtime(node) for node in all_recomputable_banned_nodes
    ]
    from torch.utils._mode_utils import no_dispatch

    def get_saved_values_knapsack(
        memory_budget: float, node_info: NodeInfo, joint_graph: fx.Graph
    ) -> tuple[list[fx.Node], float]:
        with no_dispatch():
            (
                expected_runtime,
                saved_node_idxs,
                recomputable_node_idxs,
            ) = _optimize_runtime_with_given_memory(
                joint_graph,
                memories_banned_nodes,
                runtimes_banned_nodes,
                max(memory_budget, 0),
                node_info,
                all_recomputable_banned_nodes,
            )
        dont_ban: OrderedSet[fx.Node] = OrderedSet()
        for idx in recomputable_node_idxs:
            # if idx in all_recomputable_banned_nodes:
            try:
                dont_ban.add(all_recomputable_banned_nodes[idx])
            except BaseException:
                pass

        if not dont_ban.issubset(all_recomputable_banned_nodes):
            raise AssertionError(
                "dont_ban must be a subset of all_recomputable_banned_nodes"
            )

        saved_values, _ = solve_min_cut(
            joint_graph,
            node_info,
            aggressive_options,
            dont_ban,
        )
        if AOT_PARTITIONER_DEBUG:
            create_structured_trace_for_min_cut_info(
                joint_graph=joint_graph,
                all_recomputable_banned_nodes=all_recomputable_banned_nodes,
                saved_node_idxs=saved_node_idxs,
                recomputable_node_idxs=recomputable_node_idxs,
                expected_runtime=expected_runtime,
                memories_banned_nodes=[
                    _size_of(i) for i in all_recomputable_banned_nodes
                ],
                normalized_memories_banned_nodes=memories_banned_nodes,
                runtimes_banned_nodes=runtimes_banned_nodes,
                min_cut_saved_values=saved_values,
                memory_budget=memory_budget,
                min_act_size=min_act_size,
                max_act_size=max_act_size,
                saved_values_act_size=estimate_activations_size(saved_values),
                more_aggressive_saved_values_mem_ratio=more_aggressive_saved_values_mem_ratio,
                aggressive_recomputation_saved_values_mem_ratio=aggressive_recomputation_saved_values_mem_ratio,
            )
        return saved_values, expected_runtime

    if config.visualize_memory_budget_pareto:

        def estimate_for_budget(b: float) -> tuple[float, float, float]:
            saved_values, expected_runtime = get_saved_values_knapsack(
                b, node_info=node_info, joint_graph=joint_graph
            )
            return (
                b,
                sum(runtimes_banned_nodes) - expected_runtime,
                get_mem_ratio(saved_values),
            )

        options = [estimate_for_budget(0.0), estimate_for_budget(1.0)]

        if options[0][1:] != options[1][1:]:
            bisects = [(options[0], options[1])]
            while bisects:
                lhs, rhs = bisects.pop()
                if rhs[0] - lhs[0] < 1e-3:
                    options.append(lhs)
                    options.append(rhs)
                    continue
                mid = estimate_for_budget((lhs[0] + rhs[0]) / 2)
                if mid[1:] != lhs[1:]:
                    bisects.append((lhs, mid))
                if mid[1:] != rhs[1:]:
                    bisects.append((mid, rhs))
        options.sort()

        import matplotlib.pyplot as plt

        x_values = [item[2] for item in options]
        y_values = [item[1] for item in options]

        # Plotting the values with updated axis labels and chart title
        plt.figure(figsize=(10, 6))
        plt.plot(x_values, y_values, marker="o")

        # Adding labels for each point
        for i, txt in enumerate(x_values):
            plt.annotate(
                f"{txt:.4f}",
                (txt, y_values[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )

        plt.xlabel("Memory Budget")
        plt.ylabel("Runtime of Recomputed Components")
        plt.title("Pareto Frontier of Memory Budget vs. Recomputation Runtime")
        plt.grid(True)
        fig = plt.gcf()
        plt.show()
        fig_dir = os.getcwd()
        if config.memory_budget_pareto_dir is not None:
            fig_dir = config.memory_budget_pareto_dir
            os.makedirs(fig_dir, exist_ok=True)
        rank_suffix = ""
        if torch.distributed.is_available() and torch.distributed.is_initialized():
            rank_suffix = f"_rank_{torch.distributed.get_rank()}"
        fig_name = os.path.join(
            fig_dir, f"memory_budget_pareto{rank_suffix}_{get_aot_graph_name()}.svg"
        )
        fig.savefig(fig_name)
        log.warning("Generated Pareto frontier curve at %s", fig_name)

    # todo(chilli): Estimated doesn't align exactly with actual - actual is
    # usually less memory than estimated. i'm guessing (actually quite
    # unsure about this) that's because estimated is just only including
    # tensors we actually banned from recompute, but there may be other
    # tensors that we choose to save.

    return get_saved_values_knapsack(
        memory_budget=memory_budget, node_info=node_info, joint_graph=joint_graph
    )[0]
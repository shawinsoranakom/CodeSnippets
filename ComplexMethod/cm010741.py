def solve_min_cut(
    joint_graph: fx.Graph,
    node_info: NodeInfo,
    min_cut_options: MinCutOptions,
    dont_ban: OrderedSet[fx.Node] | None = None,
) -> tuple[list[fx.Node], OrderedSet[fx.Node]]:
    if dont_ban is None:
        dont_ban = OrderedSet()
    op_types = get_default_op_list()

    if AOT_PARTITIONER_DEBUG:
        joint_module_ops = OrderedSet(
            str(node.target._overloadpacket)
            for node in joint_graph.nodes
            if node.op == "call_function" and hasattr(node.target, "_overloadpacket")
        )
        ops_ignored = joint_module_ops - OrderedSet(
            str(i) for i in op_types.recomputable_ops
        )
        log.info("Ops banned from re-materialization: %s", ops_ignored)

    def can_fuse_into_auto_functionalized(a: fx.Node, b: fx.Node) -> bool:
        if b.target != torch.ops.higher_order.auto_functionalized:
            return False
        mutable_op = b.args[0]
        (
            mutable_arg_names,
            _,
        ) = torch._higher_order_ops.auto_functionalize.get_mutable_args(
            # pyrefly: ignore[bad-argument-type]
            mutable_op
        )
        for name in mutable_arg_names:  # pyrefly: ignore [not-iterable]
            arg = b.kwargs[name]
            if a is arg:
                return True
            if isinstance(arg, list):
                if a in arg:
                    return True
        return False

    def can_fuse_into_triton_kernel_wrapper_functional(a: fx.Node, b: fx.Node) -> bool:
        if b.target != torch.ops.higher_order.triton_kernel_wrapper_functional:
            return False
        mutable_arg_names = b.kwargs["tensors_to_clone"]
        for name in mutable_arg_names:  # pyrefly: ignore [not-iterable]
            kwargs: Any = b.kwargs["kwargs"]
            if kwargs is None:
                raise AssertionError("kwargs must not be None")
            arg = kwargs[name]
            if a is arg:
                return True
        return False

    def is_fusible(a: fx.Node, b: fx.Node) -> bool:
        # We can perform "memory fusion" into a cat, but cat cannot be a
        # producer to a fusion
        if get_aten_target(b) == aten.cat:
            return True
        if can_fuse_into_auto_functionalized(a, b):
            return True
        if can_fuse_into_triton_kernel_wrapper_functional(a, b):
            return True
        if (
            a.target is operator.getitem
            and a.args[0].target  # pyrefly: ignore [missing-attribute]
            is torch.ops.higher_order.triton_kernel_wrapper_functional
        ):
            # if a is the output of a user triton kernel,
            # then (by default) we will not be able to fuse b into it
            return False
        return op_types.is_fusible(a) and op_types.is_fusible(b)

    try:
        import networkx as nx
    except ImportError as e:
        raise RuntimeError(
            "Need networkx installed to perform smart recomputation heuristics"
        ) from e

    def is_materialized_backwards(node: fx.Node) -> bool:
        if op_types.is_view(node):
            return False
        cur_nodes = OrderedSet([node])
        while len(cur_nodes) > 0:
            cur = cur_nodes.pop()
            for user in cur.users:
                if not node_info.is_required_fw(user) and not is_fusible(cur, user):
                    return True
                if op_types.is_view(user):
                    cur_nodes.add(user)

        return False

    def should_ban_recomputation(node: fx.Node) -> str | None:
        """Returns reason string if node should be banned from recomputation, None otherwise."""
        if node.op != "call_function":
            return None
        if node.target is operator.getitem:
            return None
        if node.meta.get("recompute", None) == CheckpointPolicy.MUST_SAVE:
            return "marked MUST_SAVE"
        if config.recompute_views and op_types.is_view(node):
            return None
        if node.target in [aten.lift_fresh_copy.default, aten.lift_fresh.default]:
            return None

        if min_cut_options.ban_if_not_in_allowlist:
            if not op_types.is_recomputable(node):
                return "not in recomputable allowlist"
        else:
            if op_types.is_random(node):
                return "random op"
            if op_types.is_compute_intensive(node):
                return "compute intensive op"
            if is_non_builtin_to_include(node):
                return "non-builtin op"

        # If a node *must* be materialized in the backwards pass, then we
        # should never recompute it. This is a pretty subtle point.  In
        # general, the assumption we make is that recomputing a node in the
        # backwards pass is "free". However, if a node must be materialized
        # in the backwards pass, then recomputing it is never free.
        if min_cut_options.ban_if_materialized_backward and is_materialized_backwards(
            node
        ):
            log.debug("materialized backwards: %s %s", node, tuple(node.users))
            return "materialized in backward"

        # Arbitrary hack that sometimes seems to help things. The above
        # modification appears to have made this heuristic a lot less critical
        # for performance.
        # NB: As of PR #121692, this hack no longer seems necessary.
        if (
            # pyrefly: ignore [missing-attribute]
            node.dist_from_bw < 1000 and node.dist_from_bw > config.max_dist_from_bw
        ):
            return "too far from backward"

        # If the output of an op is 4x smaller (arbitrary choice),
        # then we don't allow recomputation. The idea here is that for
        # things like reductions, saving the output of the reduction is very
        # cheap/small, and it makes sure we don't do things like recompute
        # normalizations in the backwards.
        if min_cut_options.ban_if_reduction:
            input_tensors_size = sum(
                _size_of(i) for i in node.args if isinstance(i, fx.Node)
            )
            output_size = _size_of(node)
            if output_size * 4 < input_tensors_size:
                return "reduction op"
        return None

    def is_materialized(node: fx.Node) -> bool:
        if node.op == "placeholder":
            return True

        return not all(is_fusible(node, user) for user in node.users)

    def get_node_weight(
        node: fx.Node, static_lifetime_input_nodes: OrderedSet[fx.Node]
    ) -> tuple[float, str | None]:
        """Returns (weight, cannot_save_reason).

        cannot_save_reason is None for finite weights, or a string explaining
        why the node cannot be saved for infinite weights.
        """
        if (
            config.treat_parameters_as_free_to_save
            and node in static_lifetime_input_nodes
        ):
            return 0, None
        mem_sz = _size_of(node)
        if config.recompute_views and op_types.is_view(node):
            # If `config.recompute_views=True`, we don't save views. This is generally
            # a good idea since views are free to recompute, and it makes it a bit simpler
            # to analyze.
            # NB: If they're not free to recompute (e.g. nested tensors)... I
            # think we should modify checks for view_ops to `is_view` and check
            # that. Basically, with nested tensors, `aten.view` is not a "view
            # op".
            return math.inf, "view op (recompute_views=True)"

        if isinstance(node.meta["val"], py_sym_types):
            # We never want to save symfloats
            if not isinstance(node.meta["val"], torch.SymInt):
                return INT_INF, "SymFloat (non-SymInt symbolic value)"

        # Heuristic to bias towards nodes closer to the backwards pass
        # Complete guess about current value
        mem_sz = int(
            # pyrefly: ignore [missing-attribute]
            mem_sz * (1.1 ** max(min(node.dist_from_bw, 100), 1))
        )
        if is_materialized(node):
            return mem_sz, None
        else:
            return mem_sz * 2, None

    nx_graph = nx.DiGraph()
    banned_nodes: OrderedSet[fx.Node] = OrderedSet()

    def ban_recomputation_if_allowed(node: fx.Node, reason: str = "") -> bool:
        if op_types.is_view(node):
            return False
        if node in dont_ban:
            # collectives are *always* banned from recompute, overriding `dont_ban`
            # (in particular, the activation memory budget logic is not allowed to recompute collectives)
            is_collective = (
                isinstance(node.target, torch._ops.OpOverload)
                and node.target.namespace == "_c10d_functional"
            )
            if config.unsafe_allow_optimization_of_collectives or not is_collective:
                return False
        # This bans recomputation of the node unless we've been forced not to by
        # user annotation
        if must_recompute(node):
            return False

        if "val" in node.meta and isinstance(node.meta["val"], torch.SymFloat):
            return False
        banned_nodes.add(node)
        # A node will only ever be recomputed if there is a path from an
        # ancestor of this node to the backwards path through this node that
        # doesn't go through any saved value. If this node is saved, then that
        # condition is not possible.
        nx_graph.add_edge(
            "source",
            node.name + "_in",
            capacity=math.inf,
            reason=f"cannot recompute: {reason}" if reason else "cannot recompute",
        )
        return True

    for node in joint_graph.nodes:
        if node.op == "output":
            continue

        if node in node_info.required_bw_nodes:
            # See Note: [tangents_closure vs required_bw_nodes]
            if node not in node_info.tangents_closure:
                nx_graph.add_edge(
                    node.name + "_out",
                    "sink",
                    capacity=math.inf,
                    reason="must be available for backward: input required for gradient",
                )
            else:
                nx_graph.add_edge(
                    node.name + "_in",
                    "sink",
                    capacity=math.inf,
                    reason="must be computed in backward: required for gradient",
                )
                continue

        if must_recompute(node):
            # If user explicitly says they want to recompute a node, we honor it
            # by adding an inf-capacity edge from X_in to the sink.
            # This way, X_in node is guaranteed to be part of the subgraph that contains "sink"
            # after the cut, thus guaranteeing that X op will be recomputed.
            nx_graph.add_edge(
                node.name + "_in",
                "sink",
                capacity=math.inf,
                reason="must recompute: marked by checkpoint policy",
            )
            continue

        if _is_primal(node):
            ban_recomputation_if_allowed(node, "primal input")
        elif _is_fwd_seed_offset(node):
            ban_recomputation_if_allowed(node, "forward RNG seed")

        # If a node can't be recomputed (too expensive or involves randomness),
        # we prevent it from being recomputed by adding an inf edge to the source
        # We only need to ban nodes in the fw pass, as those are the only ones that would be recomputed.
        ban_reason = should_ban_recomputation(node)
        if node_info.is_required_fw(node) and ban_reason:
            ban_recomputation_if_allowed(node, ban_reason)

        # Checks if a node is actually a tuple. Can be simplified to just an isinstance check if we always use faketensors.
        is_non_tensor_node = (
            "val" not in node.meta and "tensor_meta" not in node.meta
        ) or ("val" in node.meta and not isinstance(node.meta["val"], torch.Tensor))

        if is_sym_node(node):
            weight = float(sym_node_size(node))
            cannot_save_reason = None
        elif is_non_tensor_node:
            # FakeScriptObjects and opaque objects should have weight 0.0
            # so they can be properly partitioned between forward and
            # backward, like BackwardState.
            if isinstance(
                node.meta.get("val"), (BackwardState, FakeScriptObject)
            ) or is_opaque_node(node):
                weight = 0.0
                cannot_save_reason = None
            else:
                weight = math.inf
                cannot_save_reason = "non-tensor output"
        else:
            weight, cannot_save_reason = get_node_weight(
                node, node_info.static_lifetime_input_nodes
            )

        # Creates the weights on the "node" edge
        if cannot_save_reason and (weight == math.inf or weight == INT_INF):
            nx_graph.add_edge(
                node.name + "_in",
                node.name + "_out",
                capacity=weight,
                reason=f"cannot save: {cannot_save_reason}",
            )
        else:
            nx_graph.add_edge(node.name + "_in", node.name + "_out", capacity=weight)

        for user in node.users:
            nx_graph.add_edge(
                node.name + "_out",
                user.name + "_in",
                capacity=math.inf,
                reason="data dependency",
            )

    # todo(chilli): This is the most questionable of the 3 heuristics for banning recompute.
    # Some example models to look at where this helps perf: poolformer_m36,
    # mixer_b16_224, cait_m36_384

    # The "rough" idea here is that if you have some node that is used by both a
    # node nearby downstream as well as a node far downstream, if we recompute
    # both of the downstream nodes, we're unlikely to be able to fuse both
    # downstream nodes together.

    # Thus, we shouldn't aim to recompute far downstream nodes that depend on
    # this node. That intuition of "far downstream" is captured by whether
    # there's an unfusible op along the chain somewhere

    # It could probably be improved by properly analyzing what's going on in the
    # backwards pass instead of only relying on whether it's unfusible in the
    # forwards.

    def find_first_unfusible(start_nodes: list[fx.Node], max_range: int) -> int:
        """
        Finds the first unfusible node in the chain of nodes starting from
        `start_nodes` and returns its position.
        """
        sorted_nodes: list[tuple[int, fx.Node, bool]] = []
        for n in start_nodes:
            heapq.heappush(sorted_nodes, (node_info.get_fw_order(n), n, True))

        while len(sorted_nodes) > 0:
            _, node, node_is_fusible = heapq.heappop(sorted_nodes)
            if not node_is_fusible:
                return node_info.get_fw_order(node)
            for user in node.users:
                if node_info.is_required_fw(user):
                    if node_info.get_fw_order(user) > max_range:
                        continue
                    val: tuple[int, fx.Node, bool] = (
                        node_info.get_fw_order(user),
                        user,
                        is_fusible(node, user),
                    )
                    if val not in sorted_nodes:
                        heapq.heappush(sorted_nodes, val)
        return max_range

    if min_cut_options.ban_if_used_far_apart:
        for used_node in node_info.required_fw_nodes:
            orders = [
                node_info.get_fw_order(user)
                for user in used_node.users
                if node_info.is_required_fw(user)
            ]
            fw_users = [
                user for user in used_node.users if node_info.is_required_fw(user)
            ]
            if len(orders) > 0:
                first_unfusible_use = find_first_unfusible(fw_users, max(orders))
                for user in tuple(used_node.users):
                    if (
                        node_info.is_required_fw(user)
                        and node_info.get_fw_order(user) > first_unfusible_use
                        and is_fusible(used_node, user)
                    ):
                        if user in banned_nodes:
                            continue
                        log.info(
                            "used above/below fusible %s:(%s) -> %s -> %s:(%s)",
                            used_node,
                            node_info.get_fw_order(used_node),
                            first_unfusible_use,
                            user,
                            node_info.get_fw_order(user),
                        )
                        ban_recomputation_if_allowed(user)

    # This heuristic is fairly straightforward. The idea is that although it is
    # cheap to recompute bandwidth-bound ops, we don't want to end up in a situation
    # where we have a long chain of pointwise ops from the beginning to the end
    # of the model (like say, residual connections)

    # todo: I'm not totally sure why this heuristic matters. It's possible that this is
    # working around Inductor fusion decisions, or that it's a patch over
    # suboptimal partitioning decisions

    # Some models it improves perf on are cait_m36_384, mixer_b16_224, poolformer_m36

    if min_cut_options.ban_if_long_fusible_chains:
        visited: OrderedSet[fx.Node] = OrderedSet()
        for start_node in joint_graph.nodes:
            if not node_info.is_required_fw(start_node):
                continue
            fusible: list[tuple[int, fx.Node]] = [
                (node_info.get_fw_order(start_node), start_node)
            ]
            start_order = node_info.get_fw_order(start_node)
            while len(fusible) > 0:
                _, cur = heapq.heappop(fusible)
                if cur in visited:
                    continue
                visited.add(cur)
                # 100 is arbitrary choice to try and prevent degenerate cases
                if (
                    node_info.get_fw_order(cur) > start_order + 100
                    and len(fusible) == 0
                ):
                    log.info(
                        "too long %s %s %s %s",
                        cur,
                        start_node,
                        node_info.get_fw_order(cur),
                        node_info.get_fw_order(start_node),
                    )
                    ban_recomputation_if_allowed(cur)
                    break

                for user in cur.users:
                    if (
                        node_info.is_required_fw(user)
                        and is_fusible(cur, user)
                        and user not in banned_nodes
                    ):
                        heapq.heappush(fusible, (node_info.get_fw_order(user), user))

    try:
        cut_value, partition = nx.minimum_cut(nx_graph, "source", "sink")
    except nx.NetworkXUnbounded as unbounded_exc:
        # Check if structured tracing is enabled (for production job debugging via tlparse)
        structured_tracing_enabled = bool(trace_log.handlers)

        # Dump the FX graph for debugging
        fx_graph_file: str | None = None
        fx_graph_str: str | None = None
        joint_module = joint_graph.owning_module
        try:
            fx_graph_str = (
                joint_module.print_readable(
                    print_output=False, include_stride=True, include_device=True
                )
                if joint_module
                else str(joint_graph)
            )
            # Always log to structured trace for production debugging
            trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "min_cut_failed_fx_graph",
                    "encoding": "string",
                },
                payload_fn=lambda: fx_graph_str,
            )
            # Also write to local file for local debugging
            fx_graph_file = _get_unique_path("min_cut_failed_graph", ".txt")
            with open(fx_graph_file, "w") as f:
                f.write(fx_graph_str)
        except Exception as e:
            fx_graph_file = f"(failed to write: {e})"

        # Dump the min-cut edge list to structured trace
        edge_list_str = "\n".join(nx.readwrite.edgelist.generate_edgelist(nx_graph))
        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "min_cut_failed_edge_list",
                "encoding": "string",
            },
            payload_fn=lambda: edge_list_str,
        )

        # Find and report the infinite-capacity path
        inf_path = _find_infinite_capacity_path(nx_graph)
        if inf_path:
            # Group edges by FX node and format for user understanding
            # inf_path is a list of (from_node, to_node, reason) tuples
            #
            # Edge types and what they mean:
            # - source -> X_in: X cannot be recomputed
            # - X_in -> X_out (inf): X's output cannot be saved
            # - X_out -> Y_in: Y depends on X (data flow)
            # - X_in -> sink: X must be computed in backward
            # - X_out -> sink: X's output must be available for backward

            # Build a user-friendly explanation grouped by FX node
            node_constraints: dict[str, list[str]] = {}
            raw_path_nodes = ["source"]

            def get_base_name(node_name: str) -> str:
                for suffix in ("_in", "_out"):
                    if node_name.endswith(suffix):
                        return node_name[: -len(suffix)]
                return node_name

            for from_node, to_node, reason in inf_path:
                raw_path_nodes.append(to_node)

                # Skip source/sink, focus on FX nodes
                if from_node == "source":
                    base = get_base_name(to_node)
                    node_constraints.setdefault(base, []).append(reason)
                elif to_node == "sink":
                    base = get_base_name(from_node)
                    node_constraints.setdefault(base, []).append(reason)
                elif get_base_name(from_node) == get_base_name(to_node):
                    # Internal edge (X_in -> X_out)
                    base = get_base_name(from_node)
                    node_constraints.setdefault(base, []).append(reason)
                else:
                    # Data dependency edge (X_out -> Y_in)
                    from_base = get_base_name(from_node)
                    to_base = get_base_name(to_node)
                    node_constraints.setdefault(to_base, []).append(
                        f"depends on {from_base}"
                    )

            # Format the constraints nicely
            constraint_lines: list[str] = []
            for node_name, constraints in node_constraints.items():
                constraint_lines.append(f"  {node_name}:")
                for c in constraints:
                    constraint_lines.append(f"    - {c}")

            constraints_str = "\n".join(constraint_lines)
            raw_path_str = " -> ".join(raw_path_nodes)

            # Try to visualize (logs to structured trace and writes local file)
            svg_path, svg_content = visualize_min_cut_graph(nx_graph)
            if svg_content:
                trace_structured(
                    "artifact",
                    metadata_fn=lambda: {
                        "name": "min_cut_failed_svg",
                        "encoding": "string",
                    },
                    payload_fn=lambda: svg_content,
                )

            # Build file location messages
            local_files_msg = (
                f"FX graph dump: {fx_graph_file}\n" if fx_graph_file else ""
            )
            if svg_path:
                local_files_msg += f"Min-cut graph visualization: {svg_path}\n"

            # Suggest tlparse if structured tracing is enabled
            tlparse_msg = ""
            if structured_tracing_enabled:
                tlparse_msg = (
                    "[Production debugging: Use tlparse to extract debug artifacts "
                    "(min_cut_failed_fx_graph, min_cut_failed_edge_list, min_cut_failed_svg)]\n"
                )

            raise RuntimeError(
                f"AOT Autograd failed to partition the joint forward-backward graph.\n\n"
                f"The partitioner determines which intermediate values to save from the "
                f"forward pass vs recompute in the backward pass. This error means a value "
                f"is required for backward, but cannot be saved AND cannot be recomputed.\n\n"
                f"This is a bug in PyTorch. Please file an issue at "
                f"https://github.com/pytorch/pytorch/issues\n\n"
                f"Nodes involved in the conflict:\n"
                f"{constraints_str}\n\n"
                f"[For PyTorch developers: one of the above constraints is wrong. "
                f"Either the node should be recomputable, saveable, or not required for backward.]\n\n"
                f"[Debug: min-cut path] {raw_path_str}\n"
                f"{local_files_msg}"
                f"{tlparse_msg}"
            ) from unbounded_exc

        # Fallback if we couldn't find the path
        log.info("Failed to compute min-cut on following graph:")
        log.info(
            "%s",
            LazyString(
                lambda: "\n".join(nx.readwrite.edgelist.generate_edgelist(nx_graph))
            ),
        )
        visualize_min_cut_graph(nx_graph)
        raise
    except Exception:
        log.info("Failed to compute min-cut on following graph:")
        log.info(
            "%s",
            LazyString(
                lambda: "\n".join(nx.readwrite.edgelist.generate_edgelist(nx_graph))
            ),
        )
        visualize_min_cut_graph(nx_graph)
        raise

    reachable, non_reachable = partition
    cutset: OrderedSet[tuple[str, str]] = OrderedSet()
    for u, nbrs in ((n, nx_graph[n]) for n in reachable):
        cutset.update((u, v) for v in nbrs if v in non_reachable)

    cut_nodes: OrderedSet[str] = OrderedSet()
    for node_in, node_out in cutset:
        if node_in[:-3] != node_out[:-4]:
            raise AssertionError(
                f"node_in[:-3]={node_in[:-3]} != node_out[:-4]={node_out[:-4]}"
            )
        node_name = node_in[:-3]
        cut_nodes.add(node_name)

    name_to_node = get_name_to_node(joint_graph)
    # To make this stuff deterministic
    node_idx = {node: idx for idx, node in enumerate(joint_graph.nodes)}
    saved_values = sorted(
        (name_to_node[node] for node in cut_nodes), key=lambda x: node_idx[x]
    )
    return saved_values, banned_nodes
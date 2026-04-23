def _sync_decision_cross_ranks(
    joint_graph: torch.fx.Graph, saved_values: list[torch.fx.Node]
) -> list[torch.fx.Node]:
    # use the same policy across different GPUs
    from torch._subclasses.fake_tensor import unset_fake_temporarily

    def has_collectives(joint_graph: torch.fx.Graph) -> bool:
        for node in joint_graph.nodes:
            if isinstance(
                node.target, torch._ops.OpOverload
            ) and node.target.namespace in {"_c10d_functional", "c10d_functional"}:
                return True
        return False

    if not (
        torch.distributed.is_available()
        and torch.distributed.is_initialized()
        and torch.distributed.get_world_size() > 1
        and has_collectives(joint_graph)
    ):
        return saved_values

    canonical = _canonical_node_names(joint_graph)
    reverse_canonical = {v: k for k, v in canonical.items()}

    def has_same_nodes(joint_graph: torch.fx.Graph) -> bool:
        # Use canonical names for a hash that is invariant to node ordering
        # and naming. This correctly identifies structurally equivalent graphs
        # even when different ranks trace with different dict iteration orders.
        def _node_hash_str(n: torch.fx.Node) -> str:
            # For placeholders, n.target is the rank-local name (e.g.,
            # primals_1) which may refer to different inputs on different
            # ranks. Use only the canonical name and op for these.
            if n.op == "placeholder":
                return f"{canonical[n]}:{n.op}"
            return f"{canonical[n]}:{n.op}:{n.target}"

        node_str = "/".join(
            _node_hash_str(n)
            for n in sorted(joint_graph.nodes, key=lambda n: canonical[n])
        )
        inputs = hashlib.sha256(node_str.encode("utf-8")).hexdigest()
        all_inputs = [None for _ in range(torch.distributed.get_world_size())]
        with no_dispatch(), unset_fake_temporarily():
            # TODO: maybe use a different process group?
            torch.distributed.all_gather_object(all_inputs, inputs)
        return all(all_inputs[0] == x for x in all_inputs)

    if has_same_nodes(joint_graph):
        with no_dispatch(), unset_fake_temporarily():
            # Communicate saved values using canonical names so that
            # node names (which may differ across ranks) don't matter.
            objects = [[canonical[x] for x in saved_values]]
            saved_ops_names_all_ranks: list[list[str]] = [
                [] for _ in range(torch.distributed.get_world_size())
            ]
            torch.distributed.all_gather_object(saved_ops_names_all_ranks, objects[0])
            saved_sizes: list[int] = []
            saved_ops_with_sizes: dict[str, int] = {}

            for idx, saved_ops_names in enumerate(saved_ops_names_all_ranks):
                saved_nodes = [
                    reverse_canonical[op_name] for op_name in saved_ops_names
                ]
                saved_size = 0
                for node in saved_nodes:
                    size_of_node = _size_of(node)
                    saved_size += size_of_node
                    if idx == torch.distributed.get_rank():
                        saved_ops_with_sizes[node.name] = size_of_node
                saved_ops_with_sizes["total size"] = saved_size
                saved_sizes.append(saved_size)

            saved_sizes_tensor = torch.tensor(
                saved_sizes,
                device=torch.distributed.distributed_c10d._get_object_coll_device(),
            )
            torch.distributed.all_reduce(
                saved_sizes_tensor, op=torch.distributed.distributed_c10d.ReduceOp.MAX
            )

            picked_rank_idx = int(torch.argmin(saved_sizes_tensor).item())
            sync_decision_cross_ranks_str = f"picked_rank_idx={picked_rank_idx}, saved_nodes of current rank={saved_ops_with_sizes}"
            trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "aot_joint_graph_sync_decision_cross_ranks",
                    "encoding": "string",
                },
                payload_fn=lambda: sync_decision_cross_ranks_str,
            )

            saved_values = [
                reverse_canonical[n] for n in saved_ops_names_all_ranks[picked_rank_idx]
            ]

    return saved_values
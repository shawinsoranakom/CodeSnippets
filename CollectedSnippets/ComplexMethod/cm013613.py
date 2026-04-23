def _get_all_later_node_usages(tensor_aliases: set[Node], op_index: int) -> set[Node]:
    def _add_if_tensor(x: object, set_: set[StorageWeakRef]) -> None:
        if isinstance(x, FakeTensor):
            set_.add(StorageWeakRef(x._typed_storage()))

    nodes_used_after = set()
    for t in tensor_aliases:
        # get all nodes that use the current alias
        usage_nodes = t.users
        for n in usage_nodes:
            # We only care about usages after the current node
            if "node_idx" not in n.meta or n.meta["node_idx"] <= op_index:
                continue
            # We also don't care about intermediate view ops.
            # They only matter if their output is then used elsewhere
            # (either in an out-of-place op, or as an output to the function).
            if n in tensor_aliases:
                if (
                    isinstance(n.target, torch._ops.OpOverload)
                    or n.target is _operator.getitem
                ):
                    continue
            nodes_used_after.add(n)
    return nodes_used_after
def dedupe_symints(graph: torch.fx.Graph):
    """
    Dedupes sym ints in the graph to nodes are resolvable to symint graph inputs.

    We only dedupe from graph inputs to avoid adding a potential dependency in the forward
    from the backward.

    """

    sym_dict = _SymHashingDict()
    resolvable_from_input_symints = OrderedSet[Any]()

    for node in graph.nodes:
        val = node.meta.get("val", None)
        if val is None or not isinstance(val, py_sym_types):
            continue

        if node.op == "placeholder":
            resolvable_from_input_symints.add(node)
            sym_dict[val] = node
        elif existing_node := sym_dict.get(val):
            node.replace_all_uses_with(existing_node)
            graph.erase_node(node)
        elif all(n in resolvable_from_input_symints for n in node.all_input_nodes):
            sym_dict[val] = node
            resolvable_from_input_symints.add(node)
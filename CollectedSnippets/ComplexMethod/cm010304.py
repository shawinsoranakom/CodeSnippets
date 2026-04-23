def _common_getitem_elimination_pass(
    gm: torch.fx.GraphModule, graph_signature, module_call_graph
):
    with gm._set_replace_hook(graph_signature.get_replace_hook()):
        for module in gm.modules():
            if not isinstance(module, torch.fx.GraphModule):
                continue

            node_id: dict[torch.fx.Node, str] = {}
            getitems: dict[str, torch.fx.Node] = {}
            for node in list(module.graph.nodes):
                if node.op == "call_function" and node.target is operator.getitem:
                    source, idx = node.args
                    new_id = f"{node_id[source]}.{idx}"
                    if new_id in getitems:
                        node.replace_all_uses_with(getitems[new_id])
                        for entry in module_call_graph:
                            if entry.signature is not None:
                                entry.signature.replace_all_uses_with(
                                    node, getitems[new_id]
                                )
                        module.graph.erase_node(node)
                    else:
                        getitems[new_id] = node
                        node_id[node] = new_id
                else:
                    node_id[node] = node.name
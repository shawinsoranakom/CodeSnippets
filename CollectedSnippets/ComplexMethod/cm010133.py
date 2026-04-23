def _assign_new_node_names(
    gm: torch.fx.GraphModule,
    name_map: dict[str, str],
    custom_meta: dict[str, Any],
) -> None:
    """
    Assign new names to all nodes, in the graph module, from name map.
    """
    for node in gm.graph.nodes:
        if node.op == "placeholder":
            if node.name not in name_map:
                raise AssertionError(f"placeholder node {node.name!r} not in name_map")
            node.name = node.target = name_map[node.name]
            if node.name in custom_meta:
                if node.meta.get("custom") is None:
                    node.meta["custom"] = {}
                else:
                    # Assert if any existing key has different value
                    for k, v in node.meta["custom"].items():
                        if (
                            k in custom_meta[node.name]
                            and v != custom_meta[node.name][k]
                        ):
                            raise AssertionError(
                                f"Mismatch in custom metadata for key {k}. Value in "
                                f"node.meta is {v} and value in custom_meta is {custom_meta[node.name][k]}."
                            )
                node.meta["custom"].update(custom_meta[node.name])
            # if the constant obj is an input, we also need to update meta["val"]
            # because this is created before the placeholder naming pass
            if isinstance(node.meta["val"], CustomObjArgument):
                node.meta["val"].name = node.name
        elif node.name in name_map:
            node.name = name_map[node.name]
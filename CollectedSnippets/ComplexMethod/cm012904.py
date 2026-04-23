def fold_weight(
    quantized_model: GraphModule,
    node_name_to_scope: dict[str, tuple[str, type]],
    keep_original_weights: bool = False,
) -> GraphModule:
    """
    Trace back from the weight node util we hit getattr, reconstruct the
    graph module with the traced nodes and run the graph module to pack the
    weight. then replace the original chain of ops with the packed weight.
    """
    packed_weights = {}
    # map from folded node name to the prepacked weight name
    folded_nodes = {}
    original_weights_lookup: dict[str, list] = {}
    lookup_counter = 0
    # get packed weights
    for node in quantized_model.graph.nodes:
        if node.op == "call_function" and node.target in WEIGHT_PREPACK_OPS:
            nodes_to_fold = collect_producer_nodes(node)
            if nodes_to_fold is not None:
                for node_to_fold in nodes_to_fold:
                    folded_nodes[node_to_fold.name] = node

                prepacking_module = graph_module_from_producer_nodes(
                    quantized_model, nodes_to_fold
                )
                packed_weight = prepacking_module()
                packed_weights[node.name] = packed_weight
                if keep_original_weights:
                    original_weights = list(prepacking_module.state_dict().values())
                    original_weights_lookup[str(lookup_counter)] = sorted(
                        original_weights, key=lambda x: x.numel(), reverse=True
                    )
                    if len(original_weights_lookup[str(lookup_counter)]) == 1:
                        # bias is None
                        original_weights_lookup[str(lookup_counter)].append(None)
                    lookup_counter += 1
    lookup_counter = 0

    # remove folded nodes and replace the prepacking node with getattr
    folded_graph = Graph()
    env: dict[Any, Any] = {}

    def load_arg(a):
        return map_arg(a, lambda node: env[node.name])

    for node in quantized_model.graph.nodes:
        prepack_node = folded_nodes.get(node.name)
        if prepack_node is node:
            packed_weight = packed_weights[node.name]
            # add a prepacked attribute to root
            op_node = next(iter(prepack_node.users))
            module_path, _ = node_name_to_scope[op_node.name]
            get_new_packed_weight_name = get_new_attr_name_with_prefix(
                module_path + "_packed_weight_"
            )
            packed_weight_name = get_new_packed_weight_name(quantized_model)
            setattr(quantized_model, packed_weight_name, packed_weight)
            # replace prepack node with a getattr node
            env[node.name] = folded_graph.create_node(
                "get_attr", packed_weight_name, (), {}
            )
            if keep_original_weights:
                key_name = (
                    packed_weight_name.replace(":", "_")
                    .replace("/", "_")
                    .replace("|", "_")
                    .replace(" ", "")
                    .lower()
                )
                original_weights_lookup[key_name] = original_weights_lookup[
                    str(lookup_counter)
                ]
                del original_weights_lookup[str(lookup_counter)]
                lookup_counter += 1
        elif prepack_node is not None:
            # remove the fold node
            continue
        else:
            # copy other nodes
            env[node.name] = folded_graph.node_copy(node, load_arg)

    quantized_model = GraphModule(quantized_model, folded_graph)
    quantized_model._register_state_dict_hook(_save_packed_weight)
    quantized_model.register_load_state_dict_pre_hook(_load_packed_weight)

    if keep_original_weights:
        setattr(quantized_model, ORIGINAL_WEIGHTS_LOOKUP, original_weights_lookup)

    return quantized_model
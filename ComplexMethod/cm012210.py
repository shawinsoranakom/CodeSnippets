def merge_split_cat_aten(match: Match, *args, **kwargs):
    graph = match.graph
    split_node = match.nodes[0]
    threshold_to_cat = torch._inductor.config.post_grad_fusion_options[
        "split_cat_aten_pass"
    ].get("threshold_to_cat", 10)
    # get the getitem nodes from the split node
    getitem_nodes = list(split_node.users.keys())
    for cat_node in list(getitem_nodes[0].users.keys()):
        cat_dim = get_arg_value(cat_node, 1, "dim")
        cat_inputs = get_arg_value(cat_node, 0, "tensors")
        try:
            cat_input_len = len(cat_inputs)
        except TypeError:
            continue
        if cat_input_len < threshold_to_cat:
            continue
        # check split node and cat node has same dim, and all getitem nodes have same parent node
        parent_to_indices = defaultdict(list)  # type: ignore[var-annotated]
        parent_to_getitems = defaultdict(list)  # type: ignore[var-annotated]
        for cat_input in cat_inputs:
            # skip all non-getitem cat input
            if cat_input.target != operator.getitem:
                continue
            current_getitem_parent = cat_input.args[0]
            split_dim = get_arg_value(current_getitem_parent, 2, "dim")
            if split_dim != cat_dim:
                break
            getitem_idx = cat_input.args[1]
            if (
                current_getitem_parent not in parent_to_indices
            ) or getitem_idx != parent_to_indices[current_getitem_parent][-1][-1] + 1:
                parent_to_indices[current_getitem_parent].append([getitem_idx])
                parent_to_getitems[current_getitem_parent].append([cat_input])
            else:
                parent_to_getitems[current_getitem_parent][-1].append(cat_input)
                parent_to_indices[current_getitem_parent][-1].append(getitem_idx)

        cat_inputs_list = list(cat_inputs)
        update_cat_arg = []
        # iterate through the indices to construct the slice nodes
        for parent, indices in parent_to_indices.items():
            for idx, indice in enumerate(indices):
                start, end = indice[0], indice[-1]
                split_sections = list(parent.args[1])
                input_of_current_getitem_parent = parent.args[0]
                if len(indice) >= threshold_to_cat or len(indice) == len(
                    split_sections
                ):
                    if len(indice) != len(split_sections):
                        # get the start and end slicing indices
                        slice_node = graph.call_function(
                            torch.ops.aten.slice.Tensor,
                            args=(
                                input_of_current_getitem_parent,
                                split_dim,  # type: ignore[possibly-undefined]
                                sum(split_sections[:start]),
                                sum(split_sections[: end + 1]),
                            ),
                        )
                    else:
                        slice_node = input_of_current_getitem_parent
                    # find the index in the cat_inputs_list given the getitem node
                    update_cat_arg.append(
                        (
                            slice_node,
                            cat_inputs_list.index(parent_to_getitems[parent][idx][0]),
                            cat_inputs_list.index(parent_to_getitems[parent][idx][-1]),
                        )
                    )

        result = []
        i = 0
        for slice_tensor, start, end in update_cat_arg:
            while i < start:
                result.append(cat_inputs_list[i])
                i += 1
            result.append(slice_tensor)
            i = end + 1
        while i < len(cat_inputs_list):
            result.append(cat_inputs_list[i])
            i += 1

        cat_node.update_arg(0, result)
        for getitem_node in getitem_nodes:
            if len(getitem_node.users) == 0:
                graph.erase_node(getitem_node)
        if len(split_node.users) == 0:
            graph.erase_node(split_node)
        counters[backend]["split_cat_aten_pass"] += 1
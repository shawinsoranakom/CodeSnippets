def end_node_matches_reversed_fusion(
    end_node: Node,
    reversed_fusion: NSFusionType,
    gm: GraphModule,
    seen_nodes: set[Node],
) -> bool:
    """
    Returns true if a pattern ending with `end_node` matches
    the fusion pattern.
    """
    cur_node = end_node
    for fusion_idx in range(len(reversed_fusion)):
        # each node can only belong to one matched pattern
        if cur_node in seen_nodes:
            return False

        cur_fusion_el = reversed_fusion[fusion_idx]

        if cur_node.op == "call_function":
            fusion_el_is_fun = (not isinstance(cur_fusion_el, str)) and (
                not isinstance(cur_fusion_el, type)
            )
            if fusion_el_is_fun:
                if cur_node.target != cur_fusion_el:
                    return False
                if len(cur_node.args) > 0 and isinstance(cur_node.args[0], Node):
                    cur_node = cur_node.args[0]
                else:
                    return False
            else:
                return False

        elif cur_node.op == "call_module":
            fusion_el_is_mod = isinstance(cur_fusion_el, type)
            if fusion_el_is_mod:
                if not isinstance(cur_node.target, str):
                    raise AssertionError(f"Expected str, got {type(cur_node.target)}")
                target_mod = getattr_from_fqn(gm, cur_node.target)
                if not isinstance(cur_fusion_el, type):
                    return False
                if not isinstance(target_mod, cur_fusion_el):
                    return False
                if len(cur_node.args) > 0 and isinstance(cur_node.args[0], Node):
                    cur_node = cur_node.args[0]
                else:
                    return False
            else:
                return False

        elif cur_node.op == "call_method":
            fusion_el_is_meth_with_second_arg = (
                isinstance(cur_fusion_el, tuple) and len(cur_fusion_el) == 2
            )
            fusion_el_is_meth_without_args = isinstance(cur_fusion_el, str)
            if fusion_el_is_meth_without_args or fusion_el_is_meth_with_second_arg:
                if fusion_el_is_meth_without_args:
                    if cur_node.target != cur_fusion_el:
                        return False
                else:
                    if not isinstance(cur_fusion_el, tuple):
                        raise AssertionError(
                            f"Expected tuple, got {type(cur_fusion_el)}"
                        )
                    if cur_node.target != cur_fusion_el[0]:
                        return False
                    elif len(cur_node.args) < 2:
                        return False
                    elif cur_node.args[1] != cur_fusion_el[1]:
                        return False

                if len(cur_node.args) > 0 and isinstance(cur_node.args[0], Node):
                    cur_node = cur_node.args[0]
                else:
                    return False
            else:
                return False
        else:
            return False

    return True
def _get_subgraph_relationship_type(
    subgraph_a: NSSubgraph,
    subgraph_b: NSSubgraph,
    gm_a: GraphModule,
    gm_b: GraphModule,
    type_a_related_to_b: set[tuple[NSNodeTargetType, NSNodeTargetType]],
) -> SubgraphTypeRelationship:
    node_a = subgraph_a.base_op_node
    node_b = subgraph_b.base_op_node

    # TODO(next): make this code handle matching by what is before the base op
    if node_a.op != node_b.op:
        if not (
            node_a.op in ("call_function", "call_method")
            and node_b.op in ("call_function", "call_method")
        ):
            return SubgraphTypeRelationship.NOT_RELATED

    if node_a.op in ("call_function", "call_method"):
        key = (node_a.target, node_b.target)

        if key not in type_a_related_to_b:
            if node_a.target == node_b.target:
                return SubgraphTypeRelationship.EQUAL_BUT_UKNOWN
            else:
                return SubgraphTypeRelationship.NOT_RELATED
        # after this point, we are dealing with known types

        if node_a.target == node_b.target:
            node_a_has_prev = subgraph_a.base_op_node == subgraph_a.start_node
            node_b_has_prev = subgraph_b.base_op_node == subgraph_b.start_node
            if node_a_has_prev and (not node_b_has_prev):
                return SubgraphTypeRelationship.RELATED_BUT_NOT_EQUAL
            elif (not node_a_has_prev) and node_b_has_prev:
                return SubgraphTypeRelationship.RELATED_BUT_NOT_EQUAL
            elif (not node_a_has_prev) and (not node_b_has_prev):
                return SubgraphTypeRelationship.EQUAL
            else:
                # TODO(future PR): check for matches start_op_node and base_op_node
                return SubgraphTypeRelationship.EQUAL

        if key in type_a_related_to_b:
            return SubgraphTypeRelationship.RELATED_BUT_NOT_EQUAL
        else:
            return SubgraphTypeRelationship.NOT_RELATED
    elif node_a.op == "call_module":
        if (
            subgraph_a.base_op_node != subgraph_a.start_node
            or subgraph_b.base_op_node != subgraph_b.start_node
        ):
            raise AssertionError(
                "Matching call_module patterns where base_op_node != start_node is not supported yet"
            )
        # for call_module, we need to look up the modules to do the type check
        if not isinstance(node_a.target, str):
            raise AssertionError(f"Expected str, got {type(node_a.target)}")
        mod_a = getattr_from_fqn(gm_a, node_a.target)
        if not isinstance(node_b.target, str):
            raise AssertionError(f"Expected str, got {type(node_b.target)}")
        mod_b = getattr_from_fqn(gm_b, node_b.target)

        key = (type(mod_a), type(mod_b))

        if key not in type_a_related_to_b:
            if type(mod_a) is type(mod_b):
                return SubgraphTypeRelationship.EQUAL_BUT_UKNOWN
            else:
                return SubgraphTypeRelationship.NOT_RELATED
        elif type(mod_a) is type(mod_b):
            return SubgraphTypeRelationship.EQUAL
        else:
            return SubgraphTypeRelationship.RELATED_BUT_NOT_EQUAL

    return SubgraphTypeRelationship.NOT_RELATED
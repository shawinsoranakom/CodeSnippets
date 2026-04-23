def _get_dedup_subgraphs(matches: dict[str, _MatchResult]) -> dict[str, list[Node]]:
    # the original matches variable is unique by node, make it unique by subgraph
    # instead
    seen_nodes = set()
    subgraphs_dedup = {}

    # Dict items are not reversible until Python 3.8, so we hack it
    # to be compatible with previous Python versions
    # TODO(future PR): try reversed(list(matches.items()))
    matches_items_reversed: list[tuple[str, _MatchResult]] = list(
        reversed(matches.items())
    )

    # Note: the order is important.  `matches` currently provides the matches
    # in reverse order.  We would like to process the matches in non-reverse
    # order, so that we can create an intuitive naming scheme, such as
    # naming the first op's submodules `shadow_0_0` through `shadow_0_(n-1)`
    for name, cur_match in matches_items_reversed:  # type: ignore[call-overload]
        was_seen = False
        for node_or_tuple in cur_match[1]:
            # Cur_match[1] has an unusual type. It says that it's a `List[Node]`,
            # but it is really not. Furthermore, the contents of this field
            # can change from match results of multiple nodes of the same pattern
            #
            # For example, for conv -> bn -> relu, we see
            # match_results = {
            #   'conv': (relu, [(bn, conv), relu], ...),
            #   'bn': (relu, [(bn, conv), relu], ...),
            #   'relu': (relu, [(bn, conv), relu], ...),
            # }
            #
            # Ideally we should clean up the `find_matches` function to make
            # this more intuitive. For the purposes of this prototype, we hack
            # around it.

            if isinstance(node_or_tuple, Node):
                if node_or_tuple in seen_nodes:
                    was_seen = True
                seen_nodes.add(node_or_tuple)

            else:
                if not isinstance(node_or_tuple, tuple):
                    raise AssertionError(f"Expected tuple, got {type(node_or_tuple)}")
                for node in node_or_tuple:
                    if not isinstance(node, Node):
                        raise AssertionError(f"Expected Node, got {type(node)}")
                    if node in seen_nodes:
                        was_seen = True
                    seen_nodes.add(node)

        if was_seen:
            continue

        # Start with the unusual type, convert it to [op_0, ..., op_n]
        list_of_nodes = []

        if len(cur_match[1]) == 1:
            list_of_nodes = cur_match[1]
        else:
            if len(cur_match[1]) != 2:
                raise ValueError(
                    f"Expected cur_match[1] to have length 2, got {len(cur_match[1])}"
                )
            # either (a, b), or ((a, b), c) or (c, (a, b))
            # cannot make any assumptions on order, not clear what the
            # _find_matches function is doing to populate this
            # TODO(future PR): make this code less confusing,  see discussion
            # in https://github.com/pytorch/pytorch/pull/80521/files#r975918836

            def _order_nodes(node_a, node_b, node_c) -> list[Node]:
                nodes = [node_a, node_b, node_c]
                first_node = None
                mid_node = None
                last_node = None
                for n in nodes:
                    prev_n = n.args[0]
                    next_n = next(iter(n.users))
                    if prev_n not in nodes:
                        first_node = n
                    elif next_n not in nodes:
                        last_node = n
                    else:
                        mid_node = n
                if first_node is None or mid_node is None or last_node is None:
                    raise AssertionError("Expected all nodes to be non-None")
                if mid_node.args[0] is not first_node:
                    raise AssertionError("Expected mid_node.args[0] to be first_node")
                if last_node.args[0] is not mid_node:
                    raise AssertionError("Expected last_node.args[0] to be mid_node")
                return [last_node, mid_node, first_node]

            if isinstance(cur_match[1][0], Node) and isinstance(cur_match[1][1], Node):
                # (a, b)
                list_of_nodes = cur_match[1]
            elif isinstance(cur_match[1][0], tuple):
                # ((a, b), c)
                node_a, node_b = cur_match[1][0]
                node_c = cur_match[1][1]
                list_of_nodes = _order_nodes(node_a, node_b, node_c)
            elif isinstance(cur_match[1][1], tuple):
                # (a, (b, c))
                node_a, node_b = cur_match[1][1]
                node_c = cur_match[1][0]
                list_of_nodes = _order_nodes(node_a, node_b, node_c)

        # [node_n, ..., node_0], note that the order is reversed
        # to make it chronological for simple subgraphs
        list_of_nodes.reverse()
        subgraphs_dedup[name] = list_of_nodes

    return subgraphs_dedup
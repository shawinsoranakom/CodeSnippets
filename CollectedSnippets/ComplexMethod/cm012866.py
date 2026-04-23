def _reroute_tuple_getitem_pattern(graph: Graph):
    """
    Search for patterns where N consecutive `tuple` call_function nodes are followed by
    N consecutive `getitem` call_function nodes that are "reverses" of the `tuple` nodes.
    If we find this pattern, reroute the consumers of the last `getitem` to skip these
    N `tuple` and `getitem` nodes.

    Before:

        a   b     c
        |   \\   /
        \\   tuple
         \\   /
          tuple
            |
        getitem(1)
            |
        getitem(0)
            |
            d

    After:

        b
        |
        d
    """

    def find_patterns(
        node: Node,
        index_stack: list[int],
        current_pattern: list[Node],
        matched_patterns: list[list[Node]],
        seen: set[tuple[Node, tuple[int, ...]]],
    ):
        """
        Traverse the graph recursively to match for the N-tuple - N-getitem patterns,
        starting at the given node.

        We use a stack to keep track of the expected `getitem` indices, since these are
        reversed from the `tuple` indices. In the above example, the stack after
        (b -> tuple -> tuple) will be [0, 1], which will be popped by getitem(1) first
        and then by getitem(0).

        TODO: traverse upwards from the output and handle the case when tuple is not a
        separate node, e.g. graph.call_function(operator.getitem, args=(a, (b, c)))
        """
        if len(index_stack) == 0 and len(current_pattern) > 0:
            matched_patterns.append(copy.copy(current_pattern))
            current_pattern.clear()

        # Avoid duplicating work
        state = (node, tuple(index_stack))
        if state in seen:
            return
        seen.add(state)

        # Iterate through users of this node to find tuple/getitem nodes to match
        for user in node.users:
            if user.op == "call_function" and user.target is tuple:
                for i, user_arg in enumerate(user.args[0]):  # type: ignore[arg-type]
                    if user_arg == node:
                        index_stack.append(i)
                        current_pattern.append(user)
                        find_patterns(
                            user, index_stack, current_pattern, matched_patterns, seen
                        )
            elif user.op == "call_function" and user.target is operator.getitem:
                if len(index_stack) > 0:
                    if user.args[1] == index_stack[-1]:
                        index_stack.pop()
                        current_pattern.append(user)
                        find_patterns(
                            user, index_stack, current_pattern, matched_patterns, seen
                        )
        return matched_patterns

    # Collect all matched patterns
    matched_patterns: list[list[Node]] = []
    seen: set[tuple[Node, tuple[int, ...]]] = set()  # (node, index_stack)
    for node in graph.nodes:
        find_patterns(node, [], [], matched_patterns, seen)

    # For each pattern, redirect all consumers of the last getitem node to the correct input
    # of the first tuple node
    for pattern in matched_patterns:
        first_tuple = pattern[0]
        last_getitem = pattern[-1]
        if not (first_tuple.op == "call_function" and first_tuple.target is tuple):
            raise AssertionError(
                "first tuple node must be a call_function with target tuple"
            )
        if not (
            last_getitem.op == "call_function"
            and last_getitem.target is operator.getitem
        ):
            raise AssertionError(
                "last getitem node must be a call_function with target operator.getitem"
            )
        last_getitem_index = last_getitem.args[1]
        new_input = first_tuple.args[0][last_getitem_index]  # type: ignore[index]
        for user in list(last_getitem.users.keys()):
            user.replace_input_with(last_getitem, new_input)
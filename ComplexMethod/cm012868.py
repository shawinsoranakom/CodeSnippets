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
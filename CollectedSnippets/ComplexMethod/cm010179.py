def node_call_back(node: torch.fx.Node) -> bool:
        nonlocal enter_autocast_node_stack, first_node_after_outer_most_exit
        increment_id = False
        if first_node_after_outer_most_exit or (
            len(enter_autocast_node_stack) == 0 and _is_enter_autocast_node(node)
        ):
            if len(enter_autocast_node_stack) != 0:
                raise AssertionError(
                    f"expected empty stack, got {len(enter_autocast_node_stack)} items"
                )
            first_node_after_outer_most_exit = False
            increment_id = True
        if _is_enter_autocast_node(node):
            enter_autocast_node_stack.append(node)
        elif _is_exit_autocast_node(node):
            if len(enter_autocast_node_stack) == 0:
                raise AssertionError("enter_autocast_node_stack must not be empty")
            last_enter_autocast_node = enter_autocast_node_stack.pop()
            if node.args[0] != last_enter_autocast_node:
                raise AssertionError("exit node args[0] must match last enter node")
            if len(enter_autocast_node_stack) == 0:
                # next node should be in the next submodule since
                # autocast block ends
                first_node_after_outer_most_exit = True
        return increment_id
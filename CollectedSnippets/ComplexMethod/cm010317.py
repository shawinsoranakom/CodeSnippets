def _fix_nn_module_stacks(graph):
    # For each nn module stack in the graph, check if the fqns in it represent a stack:
    # 1. Each fqn must be a prefix of the next fqn.
    # 2. If not, remove the entries starting from the next fqn, emitting a warning.
    for node in graph.nodes:
        if "nn_module_stack" not in node.meta:
            continue

        nn_module_stack = node.meta["nn_module_stack"]
        fqns = [
            fqn.split("@")[0] if "@" in fqn else fqn
            for fqn, _t in nn_module_stack.values()
        ]

        # Check if each FQN is a prefix of the next one
        prev_fqn, *next_fqns = fqns
        num_valid_indices = 1  # root FQN
        for curr_fqn in next_fqns:
            # Check if the previous FQN is a prefix of the current one
            if _is_prefix(prev_fqn, curr_fqn):
                num_valid_indices += 1
                prev_fqn = curr_fqn
            else:
                # Found a non-prefix FQN, stop here
                break

        # If we need to remove entries, create a new stack with only valid entries
        if num_valid_indices < len(nn_module_stack):
            log.warning(
                "nn_module_stack fqns %s at node %s do not form a stack! dropping last %d entries",
                fqns,
                node,
                len(nn_module_stack) - num_valid_indices,
            )
            node.meta["nn_module_stack"] = dict(
                list(nn_module_stack.items())[:num_valid_indices]
            )
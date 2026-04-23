def _maybe_make_input_output_share_observers(
    node: Node,
    model: torch.nn.Module,
    named_modules: dict[str, torch.nn.Module],
) -> bool:
    """
    Ensures that we share an observer
    for all input arguments as well as the output argument. In detail, given
    a graph of

      x0 -> obs0 -> op -> x2
                  /
      x1 -> obs1 /

    where node obs0 points to observer instance observer0,
    obs1 points to observer1 and obs2 points to observer2, we make nodes obs1
    and ob2 point to observer0.
    Returns: whether the operation succeeded or not
    """
    first_arg = None
    # find the first non-Tensor arg
    for i in range(len(node.args)):
        if isinstance(node.args[i], (Node, list, tuple)):
            first_arg = node.args[i]
            break

    # if there is no non-Tensor arg, return directly
    if first_arg is None:
        return False

    if isinstance(first_arg, (list, tuple)):
        first_arg_arg = first_arg[0]
    elif isinstance(first_arg, Node):
        first_arg_arg = first_arg
    else:
        return False

    # if we have a graph such as
    #   observed_node -> non_observed_node -> cat
    # we need to navigate up to the first observer
    iteration_guard = 0
    # pyrefly: ignore [bad-argument-type]
    while not _is_activation_post_process_node(first_arg_arg, named_modules):
        if not isinstance(first_arg_arg, Node):
            return False
        # did not find an activation_post_process for the op
        if first_arg_arg.op == "placeholder":
            return False
        # trace back the args until we found the first Tensor/Node
        trace_back_node = None
        for i in range(len(first_arg_arg.args)):
            trace_back_node = first_arg_arg.args[i]
            if isinstance(trace_back_node, Node):
                break
        if trace_back_node is None:
            return False
        first_arg_arg = trace_back_node

        iteration_guard += 1
        if iteration_guard > 10000:
            raise AssertionError("Unable to find observer of previous node")

    if not isinstance(first_arg_arg, Node):
        raise AssertionError("first_arg_arg must be a Node")
    target_to_use = first_arg_arg.target
    if not isinstance(target_to_use, str):
        raise AssertionError("target_to_use must be a string")
    obs_mod_to_use = named_modules[target_to_use]

    if isinstance(first_arg, (list, tuple)):
        # set all other input observer nodes to use that module
        for input_idx, input_arg in enumerate(first_arg):
            if input_idx == 0:
                continue
            iteration_guard = 0
            # pyrefly: ignore [bad-argument-type]
            while not _is_activation_post_process_node(input_arg, named_modules):
                # failed to trace back since no input arg for the current node
                # pyrefly: ignore [missing-attribute]
                if len(input_arg.args) < 1:
                    return False
                # pyrefly: ignore [bad-index, unsupported-operation]
                input_arg = input_arg.args[0]
                iteration_guard += 1
                if iteration_guard > 10000:
                    raise AssertionError("Unable to find observer of previous node")

            # pyrefly: ignore [missing-attribute]
            parent_name, name = _parent_name(input_arg.target)
            setattr(named_modules[parent_name], name, obs_mod_to_use)

    # set the output observer node to use that module
    for output_obs_node in node.users:
        if not _is_activation_post_process_node(output_obs_node, named_modules):
            raise AssertionError(
                "output_obs_node must be an activation post process node"
            )
        parent_name, name = _parent_name(output_obs_node.target)
        setattr(named_modules[parent_name], name, obs_mod_to_use)

    # TODO(future PR): delete the orphaned observer modules
    return True
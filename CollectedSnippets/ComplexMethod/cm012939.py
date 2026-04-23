def create_submodule_from_subgraph(
    model: torch.nn.Module,
    first_node: Node,
    last_node: Node,
) -> GraphModule:
    """
    Input: a model, and a linear subgraph within the model from first_node to
      last_node.

    Output: a new submodule containing a copy of the subgraph, with the inputs
      to the first node becoming the inputs to the submodule, and all other
      nodes in the subgraph being copied.

    Example inputs:

    `model`: a module with graph

      x0 -> op1 -> x1 -> op2 -> x2
             |
            arg1

    `first_node`: op1
    `last_node`: op2

    Example output: a new module with graph

      input1 -> op1_copy -> x1 -> op2_copy -> output1
                   |
                  arg1
    """

    #
    # create a blank GraphModule with an empty graph
    #

    class M(torch.nn.Module):
        def forward(self, x):
            pass

    m = M()
    gm = torch.fx.symbolic_trace(m)
    g = gm.graph
    for node in reversed(gm.graph.nodes):
        g.erase_node(node)

    #
    # modify the graph to have a copy of our subgraph
    #

    cur_node_orig = first_node

    cur_name_idx = 0

    iteration_limit = 100
    cur_iteration = 0

    while True:
        if cur_node_orig is first_node:
            # we are at the first node, we need to set up graph inputs
            # TODO(future): some graphs could have placeholders which are unrelated
            # to the first node, need to handle this
            cur_args_copy = []
            cur_kwargs_copy = {}
            seen_names: set[str] = set()
            old_name_to_new_node: dict[str, Node] = {}

            def _add_placeholder(
                g: Graph, node: Node, seen_names, old_name_to_new_node
            ):
                # note: for graphs starting with patterns such as `y = x + x`, we
                # need to ensure we do not add multiple placeholders with the
                # same name
                counter = 0
                while node.name + "_" + str(counter) in seen_names:
                    counter += 1
                cur_name = node.name + "_" + str(counter)
                seen_names.add(cur_name)
                placeholder = g.placeholder(cur_name)
                old_name_to_new_node[node.name] = placeholder
                return placeholder

            for arg in cur_node_orig.args:
                if isinstance(arg, Node):
                    p = _add_placeholder(g, arg, seen_names, old_name_to_new_node)
                    cur_args_copy.append(p)
                elif isinstance(arg, (list, tuple)):
                    new_arg = []
                    for inner_arg in arg:
                        if isinstance(inner_arg, Node):
                            new_arg.append(
                                _add_placeholder(
                                    g, inner_arg, seen_names, old_name_to_new_node
                                )
                            )
                        else:
                            new_arg.append(inner_arg)
                    cur_args_copy.append(new_arg)
                else:
                    cur_args_copy.append(arg)

            # TODO(future PR): handle non-normalized kwargs
            for kwarg_name, kwarg in cur_node_orig.kwargs.items():
                if isinstance(kwarg, Node):
                    cur_kwargs_copy[kwarg_name] = _add_placeholder(
                        g, kwarg, seen_names, old_name_to_new_node
                    )
                elif isinstance(kwarg, (list, tuple)):
                    new_kwarg = []
                    for inner_kwarg in kwarg:
                        p = _add_placeholder(
                            g,
                            inner_kwarg,  # type: ignore[arg-type]
                            seen_names,
                            old_name_to_new_node,
                        )
                        new_kwarg.append(p)
                    cur_kwargs_copy[kwarg_name] = new_kwarg
                else:
                    cur_kwargs_copy[kwarg_name] = kwarg

            cur_args_copy = tuple(cur_args_copy)  # type: ignore[assignment]
        else:
            # we are not at first node, first arg is from the previous node,
            # and all other args are copied

            # the current implementation is simplistic and cannot handle
            # ops with two or more arguments which need to be passed from
            # the previous op, so we assert them out
            if cur_node_orig.target in BINARY_FUNCTIONS:
                raise AssertionError(
                    f"Unexpected binary function target: {cur_node_orig.target}"
                )

            # at this point in the code, cur_node_copy is pointing to the copy
            # of the previous node
            # TODO(future PR): this is not handling complicated graphs correctly, need to
            # look at actual relationships instead of assuming sequential graph
            # TODO(future PR): this is ignoring kwargs, will need to support kwargs
            # for any fusion pattern which has them for a node that is not the
            # first node.
            cur_args_copy = [cur_node_copy]  # type: ignore[has-type, possibly-undefined]  # noqa: F821

            if len(cur_node_orig.args) > 1:
                for arg in cur_node_orig.args[1:]:
                    if isinstance(arg, torch.nn.Parameter):
                        new_arg = arg.detach().clone()  # type: ignore[assignment]
                        mod_name = f"mod_{cur_name_idx}"
                        cur_name_idx += 1
                        setattr(gm, mod_name, new_arg)
                        new_arg_placeholder = gm.placeholder(mod_name)  # type: ignore[operator]
                        cur_args_copy.append(new_arg_placeholder)
                    elif isinstance(arg, (float, int, torch.dtype)):
                        # pyrefly: ignore [bad-argument-type]
                        cur_args_copy.append(arg)
                    else:
                        raise AssertionError(f"arg of type {type(arg)} not handled yet")
            cur_args_copy = tuple(cur_args_copy)  # type: ignore[assignment]

        # copy the node
        if cur_node_orig.op == "call_module":
            orig_mod = getattr_from_fqn(model, cur_node_orig.target)  # type: ignore[arg-type]
            orig_mod_copy = copy.deepcopy(orig_mod)
            mod_name = f"mod_{cur_name_idx}"
            setattr(gm, mod_name, orig_mod_copy)
            cur_name_idx += 1
            cur_node_copy = g.call_module(mod_name, cur_args_copy, cur_kwargs_copy)  # type: ignore[possibly-undefined,arg-type]

        elif cur_node_orig.op == "call_function":
            cur_node_copy = g.call_function(
                cur_node_orig.target,  # type: ignore[arg-type]
                cur_args_copy,  # type: ignore[arg-type]
                cur_kwargs_copy,  # type: ignore[possibly-undefined]
            )

        elif cur_node_orig.op == "call_method":
            cur_node_copy = g.call_method(
                cur_node_orig.target,  # type: ignore[arg-type]
                cur_args_copy,  # type: ignore[arg-type]
                cur_kwargs_copy,  # type: ignore[possibly-undefined]
            )

        else:
            raise AssertionError(f"{cur_node_orig.op} not supported yet")

        if cur_node_orig is last_node:
            break

        # go to next node
        if len(cur_node_orig.users.keys()) != 1:
            raise AssertionError(
                f"{cur_node_orig} has more than 1 users, not supported yet"
            )
        cur_node_orig = next(iter(cur_node_orig.users.keys()))
        cur_iteration += 1
        if cur_iteration > iteration_limit:
            raise AssertionError("iteration limit exceeded")

    # set up outputs
    g.output(cur_node_copy)

    gm.recompile()
    return gm
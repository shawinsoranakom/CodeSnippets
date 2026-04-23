def _extract_graph_with_inputs_outputs(
    joint_graph: fx.Graph,
    inputs: list[fx.Node],
    outputs: list[fx.Node],
    outputs_descs: list[AOTOutput],
    subgraph: str | None = None,
    ignore_must_be_in_fw_bw: bool = False,
) -> fx.Graph:
    """
    Given a graph, extracts out a subgraph that takes the specified nodes as
    inputs and returns the specified outputs.

    This includes specifying non-placeholder nodes as inputs.

    The general strategy is to initialize all inputs with proxies as we
    encounter them, and trace through the graph, only keeping values which take
    in valid proxies. Then, all dead code is eliminated.
    """
    new_graph = fx.Graph()
    env: dict[fx.Node, fx.Node] = {}

    # Add new placeholder nodes in the order specified by the inputs
    for node in inputs:
        new_node = new_graph.placeholder(node.name)
        # Can't use node_copy here as we may be turning previous call_function into placeholders
        new_node.meta = node.meta
        # pyrefly: ignore [unsupported-operation]
        env[node] = new_node

    for node in joint_graph.nodes:
        if not ignore_must_be_in_fw_bw:
            if (
                _must_be_in_backward(node)
                and subgraph != "backward"
                and node not in inputs
            ):
                env[node] = InvalidNode  # type: ignore[assignment]
                continue

            if (
                _must_be_in_forward(node)
                and subgraph != "forward"
                and node not in inputs
            ):
                env[node] = InvalidNode  # type: ignore[assignment]
                continue

        if node in env:
            # Node must be one of our inputs. (Any member of env which wasn't an
            # input to start must have been created by this loop and won't be in
            # joint_graph.nodes).
            continue
        elif node.op == "placeholder":
            env[node] = InvalidNode  # type: ignore[assignment]
        elif node.op == "call_function":
            all_args = pytree.arg_tree_leaves(*node.args, **node.kwargs)
            all_args = [
                isinstance(env[x], InvalidNodeBase)
                for x in all_args
                if isinstance(x, fx.Node)
            ]
            if any(all_args):
                env[node] = InvalidNode  # type: ignore[assignment]
                continue
            # pyrefly: ignore [unsupported-operation, bad-argument-type]
            env[node] = new_graph.node_copy(node, lambda x: env[x])
        elif node.op == "get_attr":
            # pyrefly: ignore [unsupported-operation, bad-argument-type]
            env[node] = new_graph.node_copy(node, lambda x: env[x])
        elif node.op == "output":
            pass
    output_values = []
    for x, x_desc in zip(outputs, outputs_descs):
        if isinstance(x, fx.Node):
            if x not in env:
                raise RuntimeError(f"Node {x} couldn't be found in env")
            if isinstance(env[x], InvalidNodeBase):
                # For forward outputs that are invalid (depend on backward), try
                # to find a valid replacement.
                replacement = None
                # For copy_ nodes that are backward-only, use the destination
                # (first arg) which is the original input.
                if (
                    x.target is torch.ops.aten.copy_.default
                    and _must_be_in_backward(x)
                    and len(x.args) >= 1
                    and isinstance(x.args[0], fx.Node)
                    and x.args[0] in env
                    and not isinstance(env[x.args[0]], InvalidNodeBase)
                ):
                    replacement = env[x.args[0]]
                # For view/reshape outputs that trace back to a getitem of a
                # higher-order op that mutates an input, find that input.
                # This handles custom_function_view outputs from triton kernels.
                if replacement is None:
                    replacement = _find_input_for_invalid_output(x, env)
                if replacement is not None:
                    output_values.append(replacement)
                    continue
                raise AssertionError(f"Node {x} was invalid, but is output")
            output_values.append(env[x])
        else:
            output_values.append(x)
    out = new_graph.output(tuple(output_values))
    out.meta["desc"] = outputs_descs
    # Snapshot stack traces on the output node before passes run,
    # as later passes may strip stack_trace from individual nodes.
    out.meta["output_stack_traces"] = [
        v.meta.get("stack_trace") if isinstance(v, fx.Node) else None
        for v in output_values
    ]

    new_graph.eliminate_dead_code()
    new_graph.lint()
    return new_graph
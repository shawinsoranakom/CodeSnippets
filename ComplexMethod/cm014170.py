def are_same_graph_modules(
    fn_name: str, a_mod: GraphModule, b_mod: GraphModule, fake_mode: "FakeTensorMode"
) -> bool:
    from torch._subclasses._fake_tensor_utils import _CacheKeyState
    from torch._subclasses.fake_tensor import extract_tensor_metadata

    # Maps the equivalent nodes from a to b
    # pyrefly: ignore [implicit-any]
    node_map = {}

    def check_all_args(a_nodes: Iterable[Any], b_nodes: Iterable[Any]) -> bool:
        for arg_a, arg_b in zip(a_nodes, b_nodes):
            if isinstance(arg_a, torch.fx.Node):
                if node_map[arg_a] != arg_b:
                    return False
            elif isinstance(arg_a, slice):
                if not isinstance(arg_b, slice):
                    return False
                if not check_all_args(
                    (arg_a.start, arg_a.stop, arg_a.step),
                    (arg_b.start, arg_b.stop, arg_b.step),
                ):
                    return False
            elif arg_a != arg_b:
                # This is a catch-all for everything else. `slice` was a
                # surprise but can there be other data structures that can
                # contain fx.Nodes in them?
                return False
        return True

    for a_node, b_node in zip(a_mod.graph.nodes, b_mod.graph.nodes):
        if a_node.op != b_node.op:
            return False

        if a_node.op == "placeholder":
            a_value = a_node.meta["example_value"]
            b_value = b_node.meta["example_value"]

            if isinstance(a_value, torch.Tensor):
                if not isinstance(b_value, torch.Tensor):
                    return False
                # Extract fake tensor metadata for a and b and then compare
                # pyrefly: ignore [implicit-any]
                a_result = []
                state = _CacheKeyState(fake_mode.shape_env)
                a_metadata = extract_tensor_metadata(a_value)
                a_metadata._flatten_into(a_result, fake_mode, state)

                b_result = []
                state = _CacheKeyState(fake_mode.shape_env)
                b_metadata = extract_tensor_metadata(b_value)
                b_metadata._flatten_into(b_result, fake_mode, state)
                if a_result != b_result:
                    return False
            elif isinstance(a_value, torch.SymInt):
                if not isinstance(b_value, torch.SymInt):
                    return False
                if a_value is not b_value:
                    return False
        elif a_node.op == "call_function":
            if a_node.target is not b_node.target:
                return False
            a_flat, _ = pytree.tree_flatten((a_node.args, a_node.kwargs))
            b_flat, _ = pytree.tree_flatten((b_node.args, b_node.kwargs))
            if not check_all_args(a_flat, b_flat):
                hc_log.debug(
                    "%s: Graph comparison failed at node (call_function): %s",
                    fn_name,
                    a_node,
                )
                return False
        elif a_node.op == "call_method":
            if a_node.target != b_node.target:
                return False
            a_flat, _ = pytree.tree_flatten((a_node.args, a_node.kwargs))
            b_flat, _ = pytree.tree_flatten((b_node.args, b_node.kwargs))
            if not check_all_args(a_flat, b_flat):
                hc_log.debug(
                    "%s: Graph comparison failed at node (call_method) : %s",
                    fn_name,
                    a_node,
                )
                return False
        elif a_node.op == "output":
            a_flat, _ = pytree.tree_flatten((a_node.args, a_node.kwargs))
            b_flat, _ = pytree.tree_flatten((b_node.args, b_node.kwargs))
            if not check_all_args(a_flat, b_flat):
                hc_log.debug("%s: Graph comparison failed at the output node", fn_name)
                return False
        elif a_node.op == "get_attr":
            a_attr = getattr(a_mod, a_node.target)
            b_attr = getattr(b_mod, b_node.target)
            if isinstance(a_attr, torch.fx.GraphModule):
                if not isinstance(b_attr, torch.fx.GraphModule):
                    return False
                # This is an example of a HOP inside a HOP
                if not are_same_graph_modules(fn_name, a_attr, b_attr, fake_mode):
                    return False
            else:
                # TODO - write an example with tensor as a graph attribute in
                # the Fx graph
                raise NotImplementedError(f"get_attr with {type(a_attr)}")
        else:
            # TODO - call_module is not supported because Dynamo Fx graph does
            # not install a call_module
            raise NotImplementedError(f"Graph equivalence check saw a {a_node.op}")

        # Two nodes are equal - add them to them map
        node_map[a_node] = b_node

    return True
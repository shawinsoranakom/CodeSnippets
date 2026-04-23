def all_node_args_have_no_tensors(
    node: Node, modules: dict[str, torch.nn.Module], cache: dict[Node, bool]
) -> bool:
    """
    If we know for sure that all of this node's args have no
    tensors (are primitives), return True.  If we either
    find a tensor or are not sure, return False. Note: this
    function is not exact.
    """
    if cache and node in cache:
        return cache[node]

    result = False  # will be overwritten
    if not isinstance(node, Node):
        result = True
    elif node.op == "placeholder":
        result = False
    elif node.op == "call_module":
        if not isinstance(node.target, str):
            raise AssertionError("node.target must be a string for call_module nodes")
        if _is_activation_post_process(modules[node.target]):
            result = all_node_args_have_no_tensors(node.args[0], modules, cache)  # type: ignore[arg-type]
    elif node.op == "call_module":
        result = False
    elif node.op == "call_function" and node.target is operator.getitem:
        result = all_node_args_have_no_tensors(node.args[0], modules, cache)  # type: ignore[arg-type]
    elif node.op == "get_attr":
        result = False
    elif node.target is getattr and node.args[1] in ["ndim", "shape"]:
        # x1 = x0.ndim
        result = True
    elif node.op == "call_method" and node.target == "size":
        # x1 = x0.size(0)
        result = True
    else:
        found_one_tensor = False
        for arg in node.args:
            if isinstance(arg, list):
                for list_el in arg:
                    if isinstance(list_el, Node):
                        this_list_el_args_have_no_tensors = (
                            all_node_args_have_no_tensors(list_el, modules, cache)
                        )
                        found_one_tensor = found_one_tensor or (
                            not this_list_el_args_have_no_tensors
                        )
                        # If found_one_tensor is True, there is no point in
                        # recursing further as the end result will always
                        # be True.
                        # TODO(future PR): remove this entire function  and
                        # change to dtype inference without recursion.
                        if found_one_tensor:
                            result = not found_one_tensor
                            if cache:
                                cache[node] = result
                            return result
            elif isinstance(arg, int):
                pass
            else:
                if isinstance(arg, Node):
                    this_arg_args_have_no_tensors = all_node_args_have_no_tensors(
                        arg, modules, cache
                    )
                    found_one_tensor = found_one_tensor or (
                        not this_arg_args_have_no_tensors
                    )
                    # If found_one_tensor is True, there is no point in
                    # recursing further as the end result will always
                    # be True.
                    # TODO(future PR): remove this entire function  and
                    # change to dtype inference without recursion.
                    if found_one_tensor:
                        result = not found_one_tensor
                        if cache:
                            cache[node] = result
                        return result
                else:
                    found_one_tensor = True
            result = not found_one_tensor
    if cache:
        cache[node] = result
    return result
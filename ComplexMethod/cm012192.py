def mark_mixed_dtype(computation_node):
    computation_node_dtype = computation_node.meta["val"].dtype
    if computation_node_dtype not in (torch.float16, torch.bfloat16):
        return

    if len(computation_node.users) != 1:
        return

    computation_node_user = next(iter(computation_node.users.keys()))
    if not isinstance(computation_node_user.meta["val"], torch.Tensor):
        return

    if computation_node_user.meta["val"].dtype != torch.float32:
        return

    while computation_node_user.target in _binary_ops:
        if len(computation_node_user.users) != 1:
            return

        computation_node_user = next(iter(computation_node_user.users.keys()))

    if computation_node_user.target != prims.convert_element_type.default:
        return

    computation_node.meta["_allow_mixed_dtype_folding"] = computation_node_dtype
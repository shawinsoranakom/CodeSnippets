def get_comm_block(comm_node: fx.Node) -> CommBlock | None:
    """
    Given a collective node (e.g., allreduce), find out all the nodes belong to
    this communication.

    Args:
        comm_node(fx.Node): The target communication/collective node.
    Returns:
        The CommBlock that encapsulates the related nodes (e.g., wait_node) of
        the given comm_node.
    """
    node_list = []
    wait_nodes = []
    inputs, _ = tree_flatten((comm_node.args, comm_node.kwargs))
    input_nodes = [inp for inp in inputs if isinstance(inp, fx.Node)]
    # If the users of the wait node are following items, we consinder them
    # to be a part of the output.
    intermediate_outputs = ("split", "reshape", "getitem", "detach", "alias")

    first_user = next(iter(comm_node.users))
    if (
        len(comm_node.users) == 1
        and first_user.target is torch.ops._c10d_functional.wait_tensor.default
    ):
        # Collective with only one output
        node_list = [comm_node, first_user]
        wait_nodes.append(first_user)
    elif len(comm_node.users) > 1 and first_user.target is operator.getitem:
        # Collective with only more than one output
        node_list.append(comm_node)
        for user in comm_node.users:
            if user.target != operator.getitem:
                return None
            if len(user.users) != 1:
                return None
            wait_node = next(iter(user.users))
            if wait_node.target != torch.ops._c10d_functional.wait_tensor.default:
                return None
            wait_nodes.append(wait_node)
            node_list.append(user)
        node_list.extend(wait_nodes)
    else:
        return None

    # Identify all the outputs of this collective block.
    outputs = OrderedSet[fx.Node]()
    nodes = collections.deque(wait_nodes)
    while nodes:
        node = nodes.popleft()
        for user in node.users:
            if isinstance(user, fx.Node) and user.name.startswith(intermediate_outputs):
                nodes.append(user)
                node_list.append(user)
            else:
                outputs.add(node)
                break

    tensor_meta = input_nodes[0].meta["tensor_meta"]
    shape: torch.Size | list[torch.Size]
    if isinstance(tensor_meta, TensorMetadata):
        shape = tensor_meta.shape
    elif isinstance(tensor_meta, (list, tuple)):
        shape = [tm.shape for tm in tensor_meta]
    else:
        logger.warning("Unexpected type of tensor_meta %s", type(tensor_meta))
        return None

    return CommBlock(
        shape=shape,
        node_list=node_list,
        wait_nodes=wait_nodes,
        comm_node=comm_node,
        inputs=input_nodes,
        outputs=outputs,
    )
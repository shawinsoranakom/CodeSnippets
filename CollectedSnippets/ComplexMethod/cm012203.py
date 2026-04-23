def normalize_squeeze_default(match: Match, *args, **kwargs):
    squeeze_node = match.nodes[0]
    squeeze_input = get_arg_value(squeeze_node, 0)

    if "dim" in squeeze_node.kwargs:
        assert len(squeeze_node.args) == 1
        dim = squeeze_node.kwargs["dim"]
    elif len(squeeze_node.args) == 1:
        # squeeze(Tensor)
        dim = None
    elif len(squeeze_node.args) == 2:
        # squeeze(Tensor self, int dim)
        # squeeze(Tensor self, int[] dim)
        dim = squeeze_node.args[1]
    else:
        # squeeze(Tensor self, int[] dim) (called with varargs)
        dim = squeeze_node.args[1:]

    if isinstance(dim, Sequence) and len(dim) == 1:
        dim = dim[0]

    with match.graph.inserting_after(squeeze_node):
        if dim is None:
            new_squeeze_node = match.graph.call_function(
                torch.squeeze, args=(squeeze_input,)
            )
        else:
            new_squeeze_node = match.graph.call_function(
                torch.squeeze, args=(squeeze_input,), kwargs={"dim": dim}
            )
    squeeze_node.replace_all_uses_with(new_squeeze_node)
    new_squeeze_node.meta.update(squeeze_node.meta)
    match.graph.erase_node(squeeze_node)
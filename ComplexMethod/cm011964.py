def graph_returns_tuple(gm: GraphModule) -> bool:
    """True if a FX graph returns a tuple"""
    if not isinstance(gm, GraphModule):
        return True  # can't check this, assume true
    (rv,) = output_node(gm).args
    if isinstance(rv, (list, tuple)):
        return True
    if (
        isinstance(rv, torch.fx.node.Node)
        and hasattr(rv.target, "_schema")
        and len(rv.target._schema.returns) > 1
        and all(str(ret.type) == "Tensor" for ret in rv.target._schema.returns)
    ):
        # for graphs whose result is one node with multiple outputs
        return True
    return False
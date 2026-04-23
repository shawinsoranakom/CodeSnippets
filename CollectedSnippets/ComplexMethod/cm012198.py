def _get_dim(node: Any):
    assert isinstance(node, torch.fx.Node)
    if "dim" in node.kwargs:
        assert isinstance(node.kwargs["dim"], int)
        return node.kwargs["dim"]
    if node.target is torch.unbind:
        if len(node.args) == 2:
            assert isinstance(node.args[-1], int)
            return node.args[-1]
        return 0  # defaults to dim=0
    if node.target is torch.split:
        if len(node.args) == 3:
            assert isinstance(node.args[-1], int)
            return node.args[-1]
        return 0  # defaults to dim=0
    raise AssertionError(
        f"Can't extract `dim` from {node.target} {node.args} {node.kwargs}"
    )
def _find_producer_matmul(node: torch.fx.Node) -> _Matmul | None:
    """
    Returns producer matmul node if found, otherwise returns None.
    """
    if node.target is aten.mm.default:
        return _Matmul.from_match(match=[node])
    elif node.target is aten._scaled_mm.default:
        return _ScaledMatmul.from_match(match=[node])
    elif node.target is aten.reshape.default:
        reshape_node_1 = node

        mm_node = reshape_node_1.args[0]
        assert isinstance(mm_node, torch.fx.Node)
        if mm_node.target not in (aten.mm.default, aten._scaled_mm.default):
            return None

        reshape_node_0 = mm_node.args[0]
        assert isinstance(reshape_node_0, torch.fx.Node)
        if reshape_node_0.target != aten.reshape.default:
            return None

        if mm_node.target is aten.mm.default:
            return _Matmul.from_match(match=[reshape_node_0, mm_node, reshape_node_1])
        elif mm_node.target is aten._scaled_mm.default:
            return _ScaledMatmul.from_match(
                match=[reshape_node_0, mm_node, reshape_node_1]
            )
    return None
def propagate_where(where_node: Node) -> bool:
    cond_node, true_node, false_node = where_node.args
    assert isinstance(cond_node, Node)
    assert isinstance(true_node, Node)
    assert isinstance(false_node, Node)
    cond_meta, true_meta, false_meta = get_chunking_metas(
        [cond_node, true_node, false_node]
    )
    out_meta = get_chunking_meta(where_node)

    assert true_meta is not None
    assert false_meta is not None
    if true_meta.scale_by and not false_meta.scale_by:
        # the false_node must be all zero
        if false_node.target != aten.full.default:
            return False
        if false_node.args[1] != 0.0:
            return False
        assert out_meta is not None
        out_meta.scale_by = true_meta.scale_by
        return True
    return False
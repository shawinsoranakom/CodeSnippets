def propagate_fma(out_node: Node) -> bool:
    mul_lhs, mul_rhs, add_rhs = out_node.args[:3]
    assert isinstance(mul_lhs, Node)
    assert isinstance(mul_rhs, Node)
    assert isinstance(add_rhs, Node)
    mul_lhs_meta, mul_rhs_meta, add_rhs_meta = get_chunking_metas(
        [mul_lhs, mul_rhs, add_rhs]
    )
    assert mul_lhs_meta is not None
    assert mul_rhs_meta is not None
    add_lhs_scale_by = get_scale_by_from_metas(mul_lhs_meta, mul_rhs_meta)
    assert add_rhs_meta is not None
    if add_lhs_scale_by is add_rhs_meta.scale_by:
        update_chunking_meta(out_node, scale_by=add_lhs_scale_by)
        return True
    return False
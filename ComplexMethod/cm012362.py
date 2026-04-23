def fwd() -> PropagateStatus:
        assert isinstance(lhs_node, Node)
        assert isinstance(rhs_node, Node)
        lhs_meta = get_chunking_meta(lhs_node)
        rhs_meta = get_chunking_meta(rhs_node)

        if has_nop_chunking_meta(lhs_node) and has_nop_chunking_meta(rhs_node):
            return _bool_to_status(False)

        # only lhs is chunked
        if not has_nop_chunking_meta(lhs_node) and has_nop_chunking_meta(rhs_node):
            assert lhs_meta is not None
            return _bool_to_status(
                copy_chunking_meta(mm_node, lhs_meta) | set_chunking_meta(rhs_node)
            )

        # either lhs or rhs is chunked at the reduction dimension
        if (lhs_meta is not None and lhs_meta.chunk_dim == 1) or (
            rhs_meta is not None and rhs_meta.chunk_dim == 0
        ):
            # The output is not chunked, but need to be sum'ed up!
            return _bool_to_status(
                set_chunking_meta(mm_node, chunk_dim=None, need_sum=True)
                | update_chunking_meta(lhs_node, chunk_dim=1)
                | update_chunking_meta(rhs_node, chunk_dim=0)
            )

        return PropagateStatus.FAIL
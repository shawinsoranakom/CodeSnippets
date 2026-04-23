def bwd() -> PropagateStatus:
        assert isinstance(lhs_node, Node)
        assert isinstance(rhs_node, Node)
        out_meta = get_chunking_meta(mm_node)
        if out_meta is None:
            return _bool_to_status(False)

        # first dim of a 2D output is chunked
        ft = get_fake_tensor_from_node_arg(mm_node)
        assert ft is not None
        if ft.ndim == 2 and out_meta.chunk_dim == 0:
            rhs_meta = get_chunking_meta(rhs_node)
            assert ChunkingMeta.is_nop(rhs_meta)
            return _bool_to_status(
                copy_chunking_meta(lhs_node, mm_node) | set_chunking_meta(rhs_node)
            )

        if out_meta.need_sum:
            changed = set_chunking_meta(lhs_node, chunk_dim=1) | set_chunking_meta(
                rhs_node, chunk_dim=0
            )
            return _bool_to_status(changed)

        return PropagateStatus.FAIL
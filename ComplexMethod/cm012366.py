def propagate_bwd() -> PropagateStatus:
        assert isinstance(arg_node, Node)
        assert isinstance(reduce_dims, (tuple, list))
        out_meta = get_chunking_meta(reduce_node)
        if out_meta is None:
            return PropagateStatus.SUCCEED_NO_CHANGE
        if out_meta.chunk_dim is not None:
            assert out_meta.chunk_dim not in reduce_dims
            return _bool_to_status(copy_chunking_meta(arg_node, out_meta))

        if out_meta.chunk_dim is None and out_meta.need_sum and len(reduce_dims) == 1:
            assert reduce_node.target == aten.sum.dim_IntList
            return _bool_to_status(
                set_chunking_meta(
                    arg_node, out_meta, chunk_dim=reduce_dims[0], need_sum=False
                )
            )

        return PropagateStatus.FAIL
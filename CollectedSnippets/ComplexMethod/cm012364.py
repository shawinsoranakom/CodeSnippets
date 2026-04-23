def propagate_fwd() -> PropagateStatus:
        if len(node_args) == 0:
            return PropagateStatus.FAIL

        first_meta = get_first_chunking_meta(*non_scalar_args)
        if first_meta is None:
            return _bool_to_status(False)

        need_handle_broadcast = (
            not ignore_broadcast and first_meta.chunk_dim is not None
        )
        if (
            need_handle_broadcast
            and first_meta.chunk_dim is not None
            and _chunk_broadcasted_tensor(first_meta.chunk_dim)
        ):
            # We don't chunking a broadcasted tensor for now.
            # Can add the rule if such a use case come up
            return PropagateStatus.FAIL

        changed = set_chunking_meta_if_none(
            non_scalar_args, first_meta, lambda node: node_ndim[node] != out_ndim
        )

        for other_node in non_scalar_args:
            other_meta = get_chunking_meta(other_node)

            if need_handle_broadcast and node_ndim[other_node] != out_ndim:
                if not ChunkingMeta.is_nop(other_meta):
                    return PropagateStatus.FAIL
            else:
                if other_meta != first_meta:
                    return PropagateStatus.FAIL

        changed |= copy_chunking_meta(out_node, first_meta)
        return _bool_to_status(changed)
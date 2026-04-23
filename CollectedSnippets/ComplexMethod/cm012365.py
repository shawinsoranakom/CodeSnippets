def propagate_bwd() -> PropagateStatus:
        if not (meta := get_chunking_meta(out_node)):
            return PropagateStatus.SUCCEED_NO_CHANGE

        need_handle_broadcast = not ignore_broadcast and meta.chunk_dim is not None
        if (
            need_handle_broadcast
            and meta.chunk_dim is not None
            and _chunk_broadcasted_tensor(meta.chunk_dim)
        ):
            return PropagateStatus.FAIL

        # apply any to a list to avoid short-circuit
        changed = any(
            [  # noqa: C419
                copy_chunking_meta(node, meta)
                if not need_handle_broadcast or node_ndim[node] == out_ndim
                else set_chunking_meta(node)
                for node in non_scalar_args
            ]
        )

        # [NOTE: NOP Chunking metadata]
        # For scalar node arguments, we add a nop ChunkingMeta so the
        # propagation continues. This is mainly needed to reach the point
        # where we attach chunking metadata to tangents that need to be
        # included in the chunking subgraph.
        # This is different to having a None ChunkingMeta
        changed |= any(
            [  # noqa: C419
                set_chunking_meta(node)
                for node in scalar_args
                if get_chunking_meta(node) is None
            ]
        )

        return _bool_to_status(changed)
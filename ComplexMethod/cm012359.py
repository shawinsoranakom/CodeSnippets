def propagate_general_copy_metadata(
    out_node: Node, ignore_broadcast: bool = False
) -> _HandlerRetType:
    """
    A general propagation rules that basically copy around the chunking
    metadata.
    """
    node_args = get_args_of_node_type(out_node)
    node_is_scalar = get_node_is_scalar(node_args)
    node_ndim = get_node_ndim(node_args)

    scalar_args = [node for node in node_args if node_is_scalar[node]]
    non_scalar_args = [node for node in node_args if not node_is_scalar[node]]

    out_ndim = out_node.meta["val"].ndim

    # This general rule only allow scalar tensors without chunking meta
    if scalar_args and not all(
        ChunkingMeta.is_nop(get_chunking_meta(arg)) for arg in scalar_args
    ):
        return PropagateStatus.FAIL

    def _chunk_broadcasted_tensor(chunk_dim: int) -> bool:
        for node in non_scalar_args:
            if node_ndim[node] != out_ndim and chunk_dim >= out_ndim - node_ndim[node]:
                return True
        return False

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

    return propagate_fwd(), propagate_bwd()
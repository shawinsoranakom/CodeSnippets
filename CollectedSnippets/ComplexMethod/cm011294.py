def _batch_p2p(p2p_ops: list[dist.P2POp], desc: str | None = None) -> list[dist.Work]:
    """
    Wrapper over batch_isend_irecv that avoids coalescing for homogeneous
    batches (all-send or all-recv).  Coalescing serializes ops on a single
    CUDA stream, which causes head-of-line blocking when independent P2P ops
    could otherwise overlap.  Mixed batches still use batch_isend_irecv for
    deadlock avoidance.
    """
    if len(p2p_ops) == 0:
        return []
    desc_str = f"{desc}, " if desc else ""
    logger.debug("batch_p2p %s%s", desc_str, p2p_ops)

    op_types = {p.op for p in p2p_ops}
    if op_types == {dist.isend}:
        return [
            p.op(p.tensor, group=p.group, tag=p.tag, group_dst=p.group_peer)
            for p in p2p_ops
        ]
    if op_types == {dist.irecv}:
        return [
            p.op(p.tensor, group=p.group, tag=p.tag, group_src=p.group_peer)
            for p in p2p_ops
        ]

    return dist.batch_isend_irecv(p2p_ops)
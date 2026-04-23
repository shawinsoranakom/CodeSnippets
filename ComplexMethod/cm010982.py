def batch_p2p_ops_inplace(
    op_list: list[str],
    peer_list: list[int],
    tag_list: list[int],
    tensors: list[torch.Tensor],
    group_name: RANK_TYPES,
):
    if not dist.is_initialized():
        raise AssertionError("torch.distributed must be initialized")
    if group_name is None or group_name == "":
        group_name = c10d._get_default_group()
    resolved = _resolve_group(group_name)
    group_name = resolved if isinstance(resolved, str) else resolved.group_name
    tensors = torch.ops._c10d_functional.batch_p2p_ops(
        op_list, peer_list, tag_list, tensors, group_name
    )
    if _are_we_tracing():
        return [
            _maybe_wrap_tensor(t) if op == "irecv" else t
            for op, t in zip(op_list, tensors)
        ]
    return list(map(_maybe_wrap_tensor, tensors))
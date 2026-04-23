def _nll_loss_forward(
    x: Tensor,
    target: Tensor,
    weight: Tensor | None,
    local_weight: Tensor | None,
    reduction: int,
    ignore_index: int,
    input_shape: torch.Size,
    channel_dim: int,
    mesh: DeviceMesh,
    mesh_dim: int,
) -> tuple[Tensor, Tensor]:
    n_dims = x.dim()
    channel_dim = 1
    if n_dims < 2:
        channel_dim = 0

    def _weight_view(weight: Tensor) -> Tensor:
        if n_dims > 1:
            shape = [
                1,
            ] * n_dims
            shape[channel_dim] = weight.shape[0]
            w = weight.view(shape)
        else:
            w = weight
        return w

    if weight is not None:
        w = _weight_view(weight)
        if local_weight is None:
            raise AssertionError
        local_w = _weight_view(local_weight)
        x = x * local_w
    safe_target = torch.where(target != ignore_index, target, 0)
    safe_target_ = safe_target.unsqueeze(channel_dim)

    # The following code block is a distributed version of
    # result = -torch.gather(self, channel_dim, safe_target_).squeeze(channel_dim)
    partial_placement = _MaskPartial(offset_shape=input_shape, offset_dim=channel_dim)
    safe_target_partial_ = partial_placement._partition_value(
        safe_target_, mesh, mesh_dim
    )
    result_partial = torch.gather(x, channel_dim, safe_target_partial_)
    # an all_reduce happens here
    result_reduced = partial_placement._reduce_value(result_partial, mesh, mesh_dim)
    result = -result_reduced.squeeze(channel_dim)

    result = torch.where(target != ignore_index, result, 0)

    if reduction == Reduction.NONE.value and n_dims > 1:
        total_weight = x.new_full((), 0.0)
        return result, total_weight

    if weight is not None:
        new_shape = list(x.shape)
        new_shape[channel_dim] = -1
        # pyrefly: ignore [unbound-name]
        w = w.expand(new_shape)
        wsum = torch.gather(w, channel_dim, safe_target_).squeeze(channel_dim)
        wsum = torch.where(target != ignore_index, wsum, 0)
        total_weight = wsum.sum()
    else:
        total_weight = (target != ignore_index).sum().to(x)

    # NOTE: this is correct only on 1D DeviceMesh; o/w additional
    #       all-reduce on result and total_weight is needed
    if reduction == Reduction.SUM.value:
        result = result.sum()
    elif reduction == Reduction.MEAN.value:
        result = result.sum() / total_weight

    return result, total_weight
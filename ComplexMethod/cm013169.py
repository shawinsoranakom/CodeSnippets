def cross_entropy_loss_indices_target_reference(input, target, weight=None, ignore_index=-100,
                                                reduction='mean', label_smoothing=0.0):
    log_softmax_input = torch.log_softmax(input, 1)
    nllloss = F.nll_loss(
        log_softmax_input,
        target,
        weight,
        ignore_index=ignore_index,
        reduction=reduction)

    if label_smoothing == 0.0:
        return nllloss

    if not (0.0 < label_smoothing <= 1.0):
        raise AssertionError(f"Expected 0.0 < label_smoothing <= 1.0, got {label_smoothing}")

    input = torch.log_softmax(input, 1)
    C = input.size(1)
    if weight is not None:
        input = input * weight.view(1, C, *(1 for _ in input.shape[2:]))

    smooth_loss = -torch.sum(input, 1)

    ignore_mask = target == ignore_index
    smooth_loss.masked_fill_(ignore_mask, 0.0)

    if reduction == 'mean':
        if weight is not None:
            # TODO: This code can path can be removed if #61309 is resolved
            # loss is normalized by the weights to be consistent with nll_loss_nd
            ret = torch.sum(smooth_loss) / weight.gather(0, target.masked_select(ignore_mask.logical_not()).flatten()).sum()
        else:
            ret = torch.mean(smooth_loss.masked_select(ignore_mask.logical_not()))
    elif reduction == 'sum':
        ret = torch.sum(smooth_loss)
    else:
        ret = smooth_loss

    return (1 - label_smoothing) * nllloss + ret * (label_smoothing / C)
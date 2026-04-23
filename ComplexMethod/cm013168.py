def cross_entropy_loss_prob_target_reference(input, target, weight=None, reduction='mean',
                                             label_smoothing=0.0):
    if input.dim() < 2:
        raise AssertionError(f"Expected input.dim() >= 2, got {input.dim()}")

    input = torch.log_softmax(input, 1)
    C = input.size(1)
    if weight is None:
        weight = torch.ones(C).type_as(input)
    weight = weight.view(1, C, *(1 for _ in input.shape[2:]))

    if label_smoothing > 0.0:
        if label_smoothing > 1.0:
            raise AssertionError(f"Expected label_smoothing <= 1.0, got {label_smoothing}")
        target = (target * (1 - label_smoothing) + label_smoothing / C)

    output = -(input * target * weight).sum(dim=1)
    if reduction == 'mean':
        return output.mean()
    elif reduction == 'sum':
        return output.sum()
    return output
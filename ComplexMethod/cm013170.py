def multilabelmarginloss_reference(input, target, reduction='mean'):
    # make everything 2-dimensional
    input_dim = input.dim()
    if input.dim() < 2:
        if target.dim() >= 2:
            raise AssertionError(f"Expected target.dim() < 2, got {target.dim()}")
        input = input.unsqueeze(0) if input.dim() == 1 else input.unsqueeze(0).unsqueeze(0)
        target = target.unsqueeze(0) if target.dim() == 1 else target.unsqueeze(0).unsqueeze(0)

    n = input.size(0)
    dim = input.size(1)
    output = input.new(n).zero_()
    for i in range(n):
        output[i] = _multilabelmarginloss_reference(input[i], target[i])

    if reduction == 'mean':
        return output.mean() / dim
    elif reduction == 'sum':
        return output.sum() / dim
    elif input_dim < 2:
        # we know we have (1, C) X (1, C) -> (1,), so squeeze will get us
        # back to correct dimensionality
        return output.squeeze() / dim
    else:
        return output / dim
def multimarginloss_reference(input, target, p=1, margin=1, weight=None, reduction='mean'):
    if input.dim() < 2:
        input = input.unsqueeze(0) if input.dim() == 1 else input.unsqueeze(0).unsqueeze(0)

    target_dim = target.dim()
    if target.dim() == 0:
        target = target.unsqueeze(0)

    n = input.size(0)
    dim = input.size(1)
    output = input.new(n)
    for x in range(n):
        output[x] = _multimarginloss_reference(input[x], target[x], p, margin, weight)

    if reduction == 'mean':
        return output.mean() / dim
    elif reduction == 'sum':
        return output.sum() / dim
    elif target_dim == 0:
        return output.squeeze(0) / dim
    return output / dim
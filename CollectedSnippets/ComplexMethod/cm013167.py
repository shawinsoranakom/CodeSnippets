def nlllossNd_reference(input, target, weight=None, ignore_index=-100,
                        reduction='mean'):
    if input.dim() < 3:
        raise AssertionError(f"Expected input.dim() >= 3, got {input.dim()}")
    N = input.size(0)
    C = input.size(1)
    out_size = (N,) + input.size()[2:]
    output = torch.zeros(out_size).type_as(input)

    if weight is None:
        weight = torch.ones(C).type_as(input)
    total_weight = 0
    for tup in product(*[range(size) for size in out_size]):
        t_nx = target[tup]
        norm = 0. if ignore_index == t_nx else weight[t_nx].item()
        input_index = list(tup)
        input_index.insert(1, t_nx)
        output[tup] = -input[tuple(input_index)] * norm
        total_weight += norm

    if reduction == 'mean':
        return output.sum() / total_weight
    elif reduction == 'sum':
        return output.sum()
    return output
def try_use_slice(base, tensor):
    from torch.fx.experimental.symbolic_shapes import statically_known_true, sym_eq

    # This condition should never be triggered.
    if is_alias(base, tensor):
        return (0, 0, base.size()[0])

    # TODO is there cases can we use slice even if stride or len(sizes) are not equal?
    if not statically_known_true(sym_eq(tensor.stride(), base.stride())):
        return None
    if not statically_known_true(sym_eq(len(tensor.size()), len(base.size()))):
        return None

    dim = None
    count = 0
    for i in range(len(tensor.size())):
        if base.size()[i] != tensor.size()[i]:
            dim = i
            count = count + 1
    if count != 1:
        return None

    if tensor.storage_offset() % tensor.stride()[dim] != 0:
        return None
    start = tensor.storage_offset() // tensor.stride()[dim]
    end = start + tensor.size()[dim]
    return (dim, start, end)
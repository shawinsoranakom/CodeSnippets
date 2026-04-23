def noncontiguous_to_padded_tensor(input, shape=None):
    tensors = input.unbind()
    ntensors = len(tensors)
    if ntensors <= 0:
        raise AssertionError(f"Expected ntensors > 0, got {ntensors}")
    if shape is None:
        shape = []
        for size in tensors[0].shape:
            shape.append(size)
        for i in range(1, ntensors):
            new_shape = tensors[i].shape
            for j in range(len(shape)):
                shape[j] = max(shape[j], new_shape[j])
        shape = [ntensors] + shape
    result = tensors[0].new_zeros(shape)
    for itensor in range(ntensors):
        tensor = tensors[itensor]
        view = result[itensor]
        for idim in range(tensor.dim()):
            view = view.narrow(idim, 0, tensor.size(idim))
        view.copy_(tensor)
    return result
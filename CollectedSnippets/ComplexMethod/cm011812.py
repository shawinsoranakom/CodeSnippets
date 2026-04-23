def index_impl_helper(x, indices, check, wrap_neg=True):
    assert isinstance(indices, (list, tuple))
    x_loader = x.make_loader()
    indices, tensor_indices = check_and_broadcast_indices(indices, x.get_device())
    assert len(tensor_indices) > 0, "Must have at least one valid idx"

    indices_loaders = [i.make_loader() if i is not None else None for i in indices]
    # no guards on output size, all the guards are set in broadcast_tensors

    # We can use the first one since they are all required to be the same size
    tensor_size = list(indices[tensor_indices[0]].get_size())

    x_size = x.get_size()

    indexed_size = [x_size[i] for i in range(len(indices)) if indices[i] is not None]
    if check and 0 in indexed_size and 0 not in tensor_size:
        raise IndexError("index is out of bounds for dimension with size 0")

    indexed_size = [x_size[i] for i in range(len(indices))]
    output_size, index_inner_fn = index_output_size_and_inner_fn(
        x_size,
        indices,
        tensor_indices,
        tensor_size,
        indices_loaders,
        indexed_size,
        None,
        check=check,
        wrap_neg=wrap_neg,
    )

    def inner_fn(idx):
        return x_loader(index_inner_fn(idx))

    return output_size, inner_fn, index_inner_fn
def find_batch_size(tensors):
    """
    Find the first dimension of a tensor in a nested list/tuple/dict of tensors.
    """
    if isinstance(tensors, (list, tuple)):
        for t in tensors:
            result = find_batch_size(t)
            if result is not None:
                return result
    elif isinstance(tensors, Mapping):
        for value in tensors.values():
            result = find_batch_size(value)
            if result is not None:
                return result
    elif isinstance(tensors, (torch.Tensor, np.ndarray)):
        return tensors.shape[0] if len(tensors.shape) >= 1 else None
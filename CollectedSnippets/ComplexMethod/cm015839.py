def _slice_tensor_or_collection(value, batch_size, original_batch_size, input_ndim):
    """Recursively slice tensors in a value (tensor, list, tuple, or other).

    Only slices tensors that have the same number of dimensions as the input
    to preserve broadcasting patterns.
    """
    if isinstance(value, torch.Tensor):
        if (
            value.dim() == input_ndim  # Same ndim to preserve broadcast pattern
            and value.dim() > 0
            and value.shape[0] == original_batch_size
            and value.shape[0] > 1  # Don't slice broadcast dimensions
        ):
            return value[:batch_size]
        return value
    elif isinstance(value, (list, tuple)):
        sliced = [
            _slice_tensor_or_collection(v, batch_size, original_batch_size, input_ndim)
            for v in value
        ]
        return type(value)(sliced)
    else:
        return value
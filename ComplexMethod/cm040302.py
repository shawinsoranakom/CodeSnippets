def scatter_update(inputs, indices, updates, reduction=None):
    inputs = convert_to_tensor(inputs)
    indices = convert_to_tensor(indices, dtype="int64")
    updates = convert_to_tensor(updates, dtype=inputs.dtype)
    indices = torch.transpose(indices, 0, 1)
    idx = tuple(indices)

    outputs = torch.clone(inputs)
    if reduction is None:
        outputs[idx] = updates
    elif reduction == "add":
        # Use index_put_ with accumulate=True for proper accumulation
        outputs.index_put_(idx, updates, accumulate=True)
    elif reduction == "max":
        # Loop-based approach handles both scalar and slice updates.
        # Associative, so sequential application handles duplicates.
        indices_t = indices.T
        for i in range(indices_t.shape[0]):
            idx = tuple(indices_t[i])
            outputs[idx] = torch.maximum(outputs[idx], updates[i])
    elif reduction == "min":
        indices_t = indices.T
        for i in range(indices_t.shape[0]):
            idx = tuple(indices_t[i])
            outputs[idx] = torch.minimum(outputs[idx], updates[i])
    elif reduction == "mul":
        indices_t = indices.T
        for i in range(indices_t.shape[0]):
            idx = tuple(indices_t[i])
            outputs[idx] = outputs[idx] * updates[i]
    else:
        raise ValueError(f"Unsupported reduction: {reduction}")
    return outputs
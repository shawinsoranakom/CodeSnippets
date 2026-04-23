def sparse_categorical_crossentropy(target, output, from_logits=False, axis=-1):
    target = convert_to_tensor(target, dtype=torch.long)
    output = convert_to_tensor(output)

    if len(target.shape) == len(output.shape) and target.shape[-1] == 1:
        target = torch.squeeze(target, dim=-1)

    if len(output.shape) < 1:
        raise ValueError(
            "Argument `output` must be at least rank 1. "
            "Received: "
            f"output.shape={output.shape}"
        )
    output_shape_without_class_dim = list(output.shape)
    del output_shape_without_class_dim[axis]

    if list(target.shape) != output_shape_without_class_dim:
        raise ValueError(
            "Arguments `target` and `output` must have the same shape "
            "up until the last dimension: "
            f"target.shape={target.shape}, output.shape={output.shape}"
        )
    # Use PyTorch native cross-entropy ops to avoid allocating a full
    # one-hot matrix of shape (batch, ..., num_classes).  For large
    # vocabularies this saves gigabytes of GPU memory per step.
    # F.cross_entropy / F.nll_loss expect the class dim at position 1,
    if output.dim() == 1:
        output = output.unsqueeze(0)
        target = target.unsqueeze(0)
        squeeze = True
    else:
        squeeze = False
        class_axis = axis % output.dim()
        if class_axis != 1:
            output = output.movedim(class_axis, 1)

    if from_logits:
        result = tnn.cross_entropy(output, target, reduction="none")
    else:
        output = output / torch.sum(output, dim=1, keepdim=True)
        output = torch.clip(output, backend.epsilon(), 1.0 - backend.epsilon())
        log_prob = torch.log(output)
        result = tnn.nll_loss(log_prob, target, reduction="none")

    if squeeze:
        result = result.squeeze(0)
    return result
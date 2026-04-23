def binary_crossentropy(target, output, from_logits=False):
    target = convert_to_tensor(target)
    output = convert_to_tensor(output)

    # We only apply the squeeze fix if we are on an MPS device,
    # as this change breaks tests on other platforms that
    # expect the original tensor shape to be preserved.
    if (
        torch.backends.mps.is_available()
        and target.ndim > 1
        and output.ndim == target.ndim
        and target.shape[-1] == 1
        and output.shape[-1] == 1
    ):
        target = torch.squeeze(target, -1).contiguous()
        output = torch.squeeze(output, -1).contiguous()

    if target.shape != output.shape:
        raise ValueError(
            "Arguments `target` and `output` must have the same shape. "
            "Received: "
            f"target.shape={target.shape}, output.shape={output.shape}"
        )

    # By default, PyTorch, does reduction of `sum` over all rows,
    # change reduction to `none` to keep dim
    if from_logits:
        return tnn.binary_cross_entropy_with_logits(
            output, target, reduction="none"
        )
    else:
        output = torch.clip(output, backend.epsilon(), 1.0 - backend.epsilon())
        return tnn.binary_cross_entropy(output, target, reduction="none")
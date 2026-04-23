def rot90(array, k=1, axes=(0, 1)):
    """Rotate an array by 90 degrees in the specified plane using PyTorch.

    Args:
        array: Input tensor
        k: Number of 90-degree rotations (default=1)
        axes: Tuple of two axes that define the
            plane of rotation (defaults to `(0, 1)`).

    Returns:
        Rotated tensor
    """
    array = convert_to_tensor(array)

    if array.ndim < 2:
        raise ValueError(
            "Input array must have at least 2 dimensions. "
            f"Received: array.ndim={array.ndim}"
        )
    if len(axes) != 2 or axes[0] == axes[1]:
        raise ValueError(
            f"Invalid axes: {axes}. Axes must be a tuple "
            "of two different dimensions."
        )

    axes = tuple(axis if axis >= 0 else array.ndim + axis for axis in axes)

    if not builtins.all(0 <= axis < array.ndim for axis in axes):
        raise ValueError(
            f"Invalid axes {axes} for tensor with {array.ndim} dimensions"
        )

    rotated = torch.rot90(array, k=k, dims=axes)
    if isinstance(array, np.ndarray):
        rotated = rotated.cpu().numpy()

    return rotated
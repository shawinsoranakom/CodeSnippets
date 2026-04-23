def should_fold(tensor1: torch.Tensor, tensor2: torch.Tensor, is_out: bool) -> bool:
    # For comments of the logic of this function see eager in /native/LinearAlgebra.cpp

    t1, t2 = (tensor1, tensor2) if tensor1.ndim >= tensor2.ndim else (tensor2, tensor1)

    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if not (t1.ndim >= 3 and t2.ndim <= 2):
        return False
    if t2.requires_grad and not is_out:
        return True
    if tensor1.ndim == 2:
        return False
    if guard_or_false(t1.numel() == 0):
        return True

    t1_shape = t1.shape
    t1_stride = t1.stride()

    # Check the contiguous, we can skip the dim with size of 1
    # as aten: https://github.com/pytorch/pytorch/blob/e201460f8aa1510b4c4686627d57b69756c4b916/aten/src/ATen/TensorGeometry.cpp#L17
    expected_stride = [1]
    for size in reversed(t1_shape[1:]):
        expected_stride.append(size * expected_stride[-1])
    return all(
        guard_or_false(size == 1) or guard_or_false(left == right)
        for left, right, size in zip(
            t1_stride, list(reversed(expected_stride)), t1_shape
        )
    )
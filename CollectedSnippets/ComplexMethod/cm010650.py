def nll_loss_forward(
    self: list[int], target: list[int], weight: Optional[list[int]], reduction: int
) -> tuple[list[int], list[int]]:
    # This is taken shamelessly from the meta function in LossNLL.cpp
    self_dim = len(self)
    target_dim = len(target)
    if not (0 < self_dim <= 2):
        raise AssertionError(f"Expected 0 < self_dim <= 2, but got self_dim={self_dim}")
    if target_dim > 1:
        raise AssertionError(f"Expected target_dim <= 1, but got {target_dim}")
    no_batch_dim = self_dim == 1 and target_dim == 0
    if not (no_batch_dim or (self[0] == target[0])):
        raise AssertionError(
            f"Batch size mismatch: self[0]={self[0]}, target[0]={target[0]}"
        )
    n_classes = self[-1]
    scalar_shape: list[int] = []
    if weight is not None and not (len(weight) == 1 and weight[0] == n_classes):
        raise AssertionError(
            f"Expected weight to be None or have shape [n_classes], "
            f"got {weight} with n_classes={n_classes}"
        )
    if reduction == 0 and self_dim == 2:
        reduction_shape = [self[0]]
    else:
        reduction_shape = scalar_shape
    return reduction_shape, scalar_shape
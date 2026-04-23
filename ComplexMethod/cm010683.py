def nll_loss_backward(
    grad_output: Tensor,
    self: Tensor,
    target: Tensor,
    weight: Tensor | None,
    reduction: int,
    ignore_index: int,
    total_weight: Tensor,
) -> Tensor:
    if not (0 <= self.dim() <= 2):
        raise AssertionError(f"input tensor should be 1D or 2D, got {self.dim()}D")
    if target.dim() > 1:
        raise AssertionError(
            f"0D or 1D target tensor expected, multi-target not supported, got {target.dim()}D"
        )

    no_batch_dim = self.dim() == 1 and target.dim() == 0
    if not (no_batch_dim or (self.shape[0] == target.shape[0])):
        raise AssertionError(
            f"size mismatch (got input: {self.shape}, target: {target.shape})"
        )
    if total_weight.numel() != 1:
        raise AssertionError(
            f"expected total_weight to be a single element tensor, got: "
            f"{total_weight.shape} ({total_weight.numel()} elements)"
        )

    if weight is not None and weight.numel() != self.shape[-1]:
        raise AssertionError(
            "weight tensor should be defined either for all or no classes"
        )

    if reduction == Reduction.NONE.value and self.dim() == 2:
        if not (grad_output.dim() == 1 and grad_output.shape[0] == self.shape[0]):
            raise AssertionError(
                f"Expected a tensor of dimension 1 and tensor.size[0] == {self.shape[0]} but "
                f"got: dimension {grad_output.dim()} and tensor.size[0] == {grad_output.shape[0]}"
            )
    else:
        if not (grad_output.dim() <= 1 and grad_output.numel() == 1):
            raise AssertionError(
                f"Expected a single element grad_output tensor, but got: {grad_output.shape}"
            )

    return _nll_loss_backward(
        grad_output, self, target, weight, reduction, ignore_index, total_weight
    )
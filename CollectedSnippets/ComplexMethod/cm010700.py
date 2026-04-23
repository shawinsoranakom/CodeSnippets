def nll_loss_forward(
    self: Tensor,
    target: Tensor,
    weight: Tensor | None,
    reduction: int,
    ignore_index: int,
) -> tuple[Tensor, Tensor]:
    if not (self.dim() > 0 and self.dim() <= 2):
        raise AssertionError(f"input tensor should be 1D or 2D, got {self.dim()}D")
    if target.dim() > 1:
        raise AssertionError(
            f"0D or 1D target tensor expected, multi-target not supported, got {target.dim()}D"
        )

    no_batch_dim = self.dim() == 1 and target.dim() == 0
    if not no_batch_dim:
        torch._check(
            self.shape[0] == target.shape[0],
            lambda: f"size mismatch (got input: {self.shape}, target: {target.shape})",
        )

    n_classes = self.shape[-1]

    if weight is not None and not (weight.dim() == 1 and weight.numel() == n_classes):
        raise AssertionError(
            f"weight tensor should be defined either for all {n_classes} classes or no classes "
            f"but got weight tensor of shape: {weight.shape}"
        )

    return _nll_loss_forward(self, target, weight, reduction, ignore_index)
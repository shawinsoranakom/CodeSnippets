def bmm(
    self: torch.Tensor,
    batch2: torch.Tensor,
    out_dtype: torch.dtype | None = None,
) -> torch.Tensor:
    # Outer-product specialization: [B, M, 1] x [B, 1, N] -> [B, M, N].
    # This avoids introducing a reduction and maps directly to broadcasted mul.
    if statically_known_true(self.shape[2] == 1) and statically_known_true(
        batch2.shape[1] == 1
    ):
        return (self * batch2).contiguous()

    # TODO: Re-enable for mps once our reductions are performant enough
    # (https://github.com/pytorch/pytorch/issues/150121)
    if config.coordinate_descent_tuning and self.device.type not in ["cpu", "mps"]:
        if statically_known_true(self.shape[1] == 1) or statically_known_true(
            batch2.shape[2] == 1
        ):
            out = (self.unsqueeze(-1) * batch2.unsqueeze(1)).sum(dim=2)
            return out
    if self.device.type == "cpu":
        if statically_known_true(self.size(1) == 1) and statically_known_true(
            batch2.size(-1) == 1
        ):
            counters["inductor"]["decompose_bmm"] += 1
            return torch.sum(
                self.squeeze(1) * batch2.squeeze(-1), dim=1, keepdim=True
            ).unsqueeze(1)
    return NotImplemented
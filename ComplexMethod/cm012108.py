def mm(
    self: torch.Tensor,
    input2: torch.Tensor,
    out_dtype: torch.dtype | None = None,
) -> torch.Tensor:
    # Our matrix vector multiplies only achieve peak bandwidth with coordinate descent tuning.
    # todo: Look into why and fix it (hopefully)

    # TODO: Re-enable for mps once our reductions are performant enough
    # (https://github.com/pytorch/pytorch/issues/150121)
    if config.coordinate_descent_tuning and self.device.type not in ["cpu", "mps"]:
        if statically_known_true(self.shape[0] == 1) or statically_known_true(
            input2.shape[1] == 1
        ):
            return (self.unsqueeze(2) * input2.unsqueeze(0)).sum(dim=1)
    # Non-CPU/MPS: always decompose. CPU: only for small tensors.
    if (
        statically_known_true(self.size(-1) == 1)
        and statically_known_true(self.size(0) != 1)
        and statically_known_true(input2.size(1) != 1)
    ):
        if self.device.type not in ["cpu", "mps"] or (
            self.device.type == "cpu"
            and statically_known_true(self.size(0) > 0)
            and statically_known_true(input2.size(0) == 1)
            and (self.dtype == input2.dtype)
            and guard_or_false((torch.numel(self) + torch.numel(input2)) <= 32)
        ):
            counters["inductor"]["decompose_mm"] += 1
            return self * input2
    if self.device.type == "cpu":
        if statically_known_true(self.size(0) == 1) and statically_known_true(
            input2.size(-1) == 1
        ):
            counters["inductor"]["decompose_mm"] += 1
            return torch.sum(
                self.squeeze(0) * input2.squeeze(-1), dim=0, keepdim=True
            ).unsqueeze(0)
    return NotImplemented
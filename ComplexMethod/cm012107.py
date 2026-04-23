def addmm(
    self: torch.Tensor,
    mat1: torch.Tensor,
    mat2: torch.Tensor,
    out_dtype: torch.dtype | None = None,
    beta: torch.types.Number = 1,
    alpha: torch.types.Number = 1,
) -> torch.Tensor:
    if mat1.device.type not in ["cpu", "mps"]:
        if (
            statically_known_true(mat1.size(-1) == 1)
            and statically_known_true(mat1.size(0) != 1)
            and statically_known_true(mat2.size(1) != 1)
        ):
            counters["inductor"]["decompose_addmm"] += 1
            out = mat1 * mat2
            return alpha * out + beta * self

    if self.device.type == "cpu":
        if statically_known_true(mat1.size(0) == 1) and statically_known_true(
            mat2.size(-1) == 1
        ):
            counters["inductor"]["decompose_addmm"] += 1
            out = torch.sum(
                mat1.squeeze(0) * mat2.squeeze(-1), dim=0, keepdim=True
            ).unsqueeze(0)
            return alpha * out + beta * self
        if (
            statically_known_true(mat1.size(0) == 1)
            and guard_or_false(mat2.size(0) <= 16)
            and guard_or_false(mat2.size(1) <= 16)
        ):
            counters["inductor"]["decompose_addmm"] += 1
            out = (mat1.T * mat2).sum(dim=0, keepdim=True)
            return alpha * out + beta * self
    return NotImplemented
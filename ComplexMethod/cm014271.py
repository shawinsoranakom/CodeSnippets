def foreach_lerp_inplace(
    self,
    end: list[torch.Tensor] | tuple[torch.Tensor, ...],
    weight: float | int | torch.Tensor,
) -> None:
    # Decompose lerp via addcmul_ for FMA.  Uses the same dual-formula
    # approach as CUDA's native lerp to get bitwise identical results:
    #   |w| <  0.5  (low):  fma(w, diff, start)
    #   |w| >= 0.5  (high): fma(-(1-w), diff, end)
    # For tensor weights (e.g. 0-dim tensor from tensor betas in Adam) the
    # low formula is always used because the native lerp_scalar lowering
    # would crash on float(weight) for symbolic expressions.
    diff = torch._foreach_sub(end, self)
    if isinstance(weight, torch.Tensor):
        # Select base and weight for the dual formula before a single addcmul:
        #   low  (|w| <  0.5): fma(w,      diff, self)
        #   high (|w| >= 0.5): fma(-(1-w), diff, end)
        mask = weight.abs() >= 0.5
        neg_omw = -(1.0 - weight)
        w = torch.where(mask, neg_omw, weight)
        bases = [torch.where(mask, e, s) for s, e in zip(self, end)]
        w_list = [w] * len(diff)
        torch._foreach_addcmul_(bases, w_list, diff)
        for s, b in zip(self, bases):
            s.copy_(b)
    else:
        abs_weight = weight if weight >= 0 else -weight
        if abs_weight >= 0.5:
            # High formula: end + (-(1-w)) * diff  →  fma(-(1-w), diff, end)
            # Compute 1-w in target dtype to match CUDA rounding.
            d0 = self[0]
            neg_omw = -(1.0 - torch.tensor(weight, dtype=d0.dtype, device=d0.device))
            neg_omw_list = [neg_omw] * len(diff)
            for s, e in zip(self, end):
                s.copy_(e)
            torch._foreach_addcmul_(self, neg_omw_list, diff)
        else:
            # Low formula: start + w * diff  →  fma(w, diff, start)
            weights = [torch.full_like(d, weight) for d in diff]
            torch._foreach_addcmul_(self, weights, diff)
    return self
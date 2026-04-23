def _no_grad_trunc_normal_(
    tensor: Tensor,
    mean: float,
    std: float,
    a: float,
    b: float,
    generator: torch.Generator | None = None,
) -> Tensor:
    # Meta tensors have no storage, so sampling is a no-op.
    if tensor.is_meta:
        return tensor

    def norm_cdf(x: float) -> float:
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    if (mean < a - 2 * std) or (mean > b + 2 * std):
        warnings.warn(
            "mean is more than 2 std from [a, b] in nn.init.trunc_normal_. "
            "The distribution of values may be incorrect.",
            stacklevel=2,
        )

    with torch.no_grad():
        p = norm_cdf((b - mean) / std) - norm_cdf((a - mean) / std)

        if p > 0.3:
            # Cast bounds to tensor dtype so the rejection mask is consistent
            # with the tensor's representable values.
            lo = tensor.new_tensor(a, device="cpu").item()
            hi = tensor.new_tensor(b, device="cpu").item()
            result = tensor.normal_(mean, std, generator=generator)
            while True:
                mask = (result < lo) | (result > hi)
                if not mask.any():
                    break
                result = torch.where(
                    mask,
                    torch.empty_like(result).normal_(mean, std, generator=generator),
                    result,
                )
            if tensor is not result:
                tensor.copy_(result)
        else:
            mode = max(a, min(mean, b))
            log_peak = -0.5 * ((mode - mean) / std) ** 2

            candidates = torch.empty_like(tensor)
            accept_buf = torch.empty_like(tensor)

            # First iteration: sample directly into tensor to avoid
            # a where() + copy_() if all samples are accepted.
            tensor.uniform_(a, b, generator=generator)
            candidates.copy_(tensor)
            # log_pdf = -0.5 * ((candidates - mean) / std) ** 2
            candidates.sub_(mean).div_(std).pow_(2).mul_(-0.5).sub_(log_peak)
            pending = accept_buf.uniform_(generator=generator).log_().gt(candidates)
            if not pending.any():
                pass
            else:
                result = tensor
                while True:
                    candidates.uniform_(a, b, generator=generator)
                    result = torch.where(pending, candidates, result)
                    # log_pdf = -0.5 * ((candidates - mean) / std) ** 2
                    candidates.sub_(mean).div_(std).pow_(2).mul_(-0.5).sub_(log_peak)
                    pending = torch.where(
                        pending,
                        accept_buf.uniform_(generator=generator).log_().gt(candidates),
                        pending,
                    )
                    if not pending.any():
                        break
                tensor.copy_(result)

        return tensor
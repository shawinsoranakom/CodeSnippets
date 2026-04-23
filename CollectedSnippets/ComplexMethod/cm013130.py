def _group_quantize_tensor(w, n_bit=4, q_group_size=16):
    if w.dim() != 2:
        raise AssertionError(f"expected w.dim() == 2, got {w.dim()}")
    w = w.transpose(0, 1).contiguous()
    if q_group_size <= 1:
        raise AssertionError(f"expected q_group_size > 1, got {q_group_size}")
    if w.shape[-1] % q_group_size != 0:
        raise AssertionError(
            f"expected w.shape[-1] % q_group_size == 0, got w.shape[-1]={w.shape[-1]}, q_group_size={q_group_size}"
        )

    to_quant = w.reshape(-1, q_group_size)
    if torch.isnan(to_quant).sum() != 0:
        raise AssertionError("to_quant contains NaN values")

    max_val = to_quant.amax(dim=1, keepdim=True)
    min_val = to_quant.amin(dim=1, keepdim=True)
    max_int = 2**n_bit - 1
    min_int = 0
    scales = (max_val - min_val).clamp(min=1e-6) / max_int
    if torch.isnan(scales).sum() != 0:
        raise AssertionError("scales contains NaN values")

    zeros = min_val + scales * (2 ** (n_bit - 1))
    if torch.isnan(zeros).sum() != 0:
        raise AssertionError("zeros contains NaN values")

    out = to_quant.sub(min_val).div(scales).round().clamp_(min_int, max_int)
    if torch.isnan(out).sum() != 0:
        raise AssertionError("out contains NaN values")

    out = out.to(dtype=torch.int32).reshape(w.shape)
    if out.device != torch.device("cpu"):
        out = (out[::, ::2] << 4 | out[::, 1::2]).to(torch.uint8)

    # Scales and zeros for the same q-group should be contiguous, so we can
    # load as a 32-bit word
    scales = scales.view(w.shape[0], -1)
    zeros = zeros.view(w.shape[0], -1)
    scales_and_zeros = (
        torch.cat(
            [
                scales.reshape(scales.size(0), scales.size(1), 1),
                zeros.reshape(zeros.size(0), zeros.size(1), 1),
            ],
            2,
        )
        .transpose(0, 1)
        .contiguous()
    )

    return out, scales_and_zeros
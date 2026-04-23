def _get_scale_zp(
        min_val: float,
        max_val: float,
        dtype: torch.dtype,
        reduce_range: bool = False,
        preserve_sparsity: bool = False) -> tuple[float, int]:
    """
    Calculate the quantization parameters (scale, zero_point)
    based on the min and max element of the tensor
    """
    if dtype == torch.qint8:
        if reduce_range:
            qmin, qmax = -64, 63
        else:
            qmin, qmax = -128, 127
    else:
        if reduce_range:
            qmin, qmax = 0, 127
        else:
            qmin, qmax = 0, 255

    if min_val < 0 and max_val > 0 and preserve_sparsity:
        symmetric_qmin = int(-((qmax - qmin) / 2 + 1))
        symmetric_qmax = int((qmax - qmin) / 2)
        max_scale = max(
            abs(min_val / symmetric_qmin), abs(max_val / symmetric_qmax)
        )
        min_val = max_scale * symmetric_qmin
        max_val = max_scale * symmetric_qmax
    min_val = min(min_val, 0.0)
    max_val = max(max_val, 0.0)
    scale = (max_val - min_val) / (qmax - qmin)
    if scale == 0.0 or math.isinf(1.0 / scale):
        scale = 0.1
        zero_point = 0

    zero_point_from_min = qmin - min_val / float(scale)
    zero_point_from_max = qmax - max_val / float(scale)
    zero_point_from_min_error = abs(qmin) - abs(min_val / float(scale))
    zero_point_from_max_error = abs(qmax) - abs(max_val / float(scale))
    if zero_point_from_min_error < zero_point_from_max_error:
        initial_zero_point = zero_point_from_min
    else:
        initial_zero_point = zero_point_from_max

    if min_val < 0 and max_val > 0 and preserve_sparsity:
        initial_zero_point = (qmin + qmax) / 2 + 1

    nudged_zero_point = 0

    if initial_zero_point < qmin:
        nudged_zero_point = qmin
    elif initial_zero_point > qmax:
        nudged_zero_point = qmax
    else:
        nudged_zero_point = int(round(initial_zero_point))

    return (scale, int(nudged_zero_point))
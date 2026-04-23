def _calculate_dynamic_qparams(X, dtype, reduce_range=False):
    """Calculate the dynamic quantization parameters (scale, zero_point)
    according to the min and max element of the tensor"""
    if isinstance(X, torch.Tensor):
        X = X.cpu().data.numpy()
    if dtype == torch.qint8:
        if reduce_range:
            qmin, qmax = -64, 63
        else:
            qmin, qmax = -128, 127
    else:  # dtype == torch.quint8
        if reduce_range:
            qmin, qmax = 0, 127
        else:
            qmin, qmax = 0, 255

    min_val = X.min().astype(dtype=np.float32)
    max_val = X.max().astype(dtype=np.float32)
    min_val = min(0.0, min_val)
    max_val = max(0.0, max_val)
    scale = (np.float64(max_val) - min_val) / (qmax - qmin)
    if scale == 0.0 or math.isinf(1.0 / scale):
        scale = np.float64(0.1)
        zero_point = 0

    zero_point_from_min = qmin - min_val / float(scale)
    zero_point_from_max = qmax - max_val / float(scale)
    zero_point_from_min_error = abs(qmin) - abs(min_val / float(scale))
    zero_point_from_max_error = abs(qmax) - abs(max_val / float(scale))
    if zero_point_from_min_error < zero_point_from_max_error:
        initial_zero_point = zero_point_from_min
    else:
        initial_zero_point = zero_point_from_max
    nudged_zero_point = 0

    if initial_zero_point < qmin:
        nudged_zero_point = qmin
    elif initial_zero_point > qmax:
        nudged_zero_point = qmax
    else:
        nudged_zero_point = int(round(initial_zero_point))

    return [scale.astype(np.float32), int(nudged_zero_point)]
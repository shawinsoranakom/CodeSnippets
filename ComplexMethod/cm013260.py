def _calculate_dynamic_qparams(X, dtype, reduce_range=False, qscheme=torch.per_tensor_affine):
    """Calculate the dynamic quantization parameters (scale, zero_point)
    according to the min and max element of the tensor"""
    if qscheme not in (torch.per_tensor_affine, torch.per_tensor_symmetric):
        raise AssertionError(
            f"Expected qscheme to be per_tensor_affine or per_tensor_symmetric, got {qscheme}"
        )
    if qscheme == torch.per_tensor_symmetric:
        if dtype != torch.qint8:
            raise AssertionError(
                f"Expected dtype to be torch.qint8 for symmetric qscheme, got {dtype}"
            )
    if isinstance(X, torch.Tensor):
        X = X.numpy()
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
    min_val = X.min()
    max_val = X.max()
    is_symmetric = (qscheme == torch.per_tensor_symmetric)
    if min_val == max_val:
        scale = 1.0
        zero_point = 0
    else:
        if is_symmetric:
            max_val = max(max_val, -min_val)
            min_val = -max_val
            scale = (max_val - min_val) / (qmax - qmin)
            scale = max(scale, np.finfo(np.float32).eps)
            zero_point = 0
        else:
            max_val = max(max_val, 0.0)
            min_val = min(min_val, 0.0)
            scale = (max_val - min_val) / (qmax - qmin)
            scale = max(scale, np.finfo(np.float32).eps)
            zero_point = qmin - round(min_val / scale)
            zero_point = max(qmin, zero_point)
            zero_point = min(qmax, zero_point)
    return [float(scale), int(zero_point)]
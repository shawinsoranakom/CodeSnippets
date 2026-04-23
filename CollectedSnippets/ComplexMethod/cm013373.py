def _xy_helper_corrcoef(x_tensor, y_tensor=None, rowvar=True):
    """Prepare inputs for cov and corrcoef."""

    # https://github.com/numpy/numpy/blob/v1.24.0/numpy/lib/function_base.py#L2636
    if y_tensor is not None:
        # make sure x and y are at least 2D
        ndim_extra = 2 - x_tensor.ndim
        if ndim_extra > 0:
            x_tensor = x_tensor.view((1,) * ndim_extra + x_tensor.shape)
        if not rowvar and x_tensor.shape[0] != 1:
            x_tensor = x_tensor.mT
        x_tensor = x_tensor.clone()

        ndim_extra = 2 - y_tensor.ndim
        if ndim_extra > 0:
            y_tensor = y_tensor.view((1,) * ndim_extra + y_tensor.shape)
        if not rowvar and y_tensor.shape[0] != 1:
            y_tensor = y_tensor.mT
        y_tensor = y_tensor.clone()

        x_tensor = _concatenate((x_tensor, y_tensor), axis=0)

    return x_tensor
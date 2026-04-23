def _runner(init, shape, target_mean=None, target_std=None,
            target_max=None, target_min=None):
    with device("cpu"):
        variable = Variable(init(shape))
    output = variable.numpy()
    lim = 3e-2
    if target_std is not None:
        assert abs(output.std() - target_std) < lim
    if target_mean is not None:
        assert abs(output.mean() - target_mean) < lim
    if target_max is not None:
        assert abs(output.max() - target_max) < lim
    if target_min is not None:
        assert abs(output.min() - target_min) < lim
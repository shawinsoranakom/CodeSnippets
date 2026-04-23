def simple_unlimited_args_kwargs_block(content, one, two="hi", *args, **kwargs):
    """Expected simple_unlimited_args_kwargs_block __doc__"""
    return (
        "simple_unlimited_args_kwargs_block - Expected result (content value: %s): "
        "%s / %s"
        % (
            content,
            ", ".join(str(arg) for arg in [one, two, *args]),
            ", ".join("%s=%s" % (k, v) for (k, v) in kwargs.items()),
        )
    )
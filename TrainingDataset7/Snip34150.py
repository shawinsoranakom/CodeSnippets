def inclusion_unlimited_args_kwargs(one, two="hi", *args, **kwargs):
    """Expected inclusion_unlimited_args_kwargs __doc__"""
    return {
        "result": "inclusion_unlimited_args_kwargs - Expected result: %s / %s"
        % (
            ", ".join(str(arg) for arg in [one, two, *args]),
            ", ".join("%s=%s" % (k, v) for (k, v) in kwargs.items()),
        )
    }
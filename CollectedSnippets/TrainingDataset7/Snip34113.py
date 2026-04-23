def simple_only_unlimited_args(*args):
    """Expected simple_only_unlimited_args __doc__"""
    return "simple_only_unlimited_args - Expected result: %s" % ", ".join(
        str(arg) for arg in args
    )
def simple_unlimited_args(one, two="hi", *args):
    """Expected simple_unlimited_args __doc__"""
    return "simple_unlimited_args - Expected result: %s" % (
        ", ".join(str(arg) for arg in [one, two, *args])
    )
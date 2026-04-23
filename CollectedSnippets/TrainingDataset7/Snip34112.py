def simple_unlimited_args_block(content, one, two="hi", *args):
    """Expected simple_unlimited_args_block __doc__"""
    return "simple_unlimited_args_block - Expected result (content value: %s): %s" % (
        content,
        ", ".join(str(arg) for arg in [one, two, *args]),
    )
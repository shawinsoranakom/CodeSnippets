def simple_one_default_block(content, one, two="hi"):
    """Expected simple_one_default_block __doc__"""
    return "simple_one_default_block - Expected result (content value: %s): %s, %s" % (
        content,
        one,
        two,
    )
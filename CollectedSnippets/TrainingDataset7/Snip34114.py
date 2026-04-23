def simple_only_unlimited_args_block(content, *args):
    """Expected simple_only_unlimited_args_block __doc__"""
    return (
        "simple_only_unlimited_args_block - Expected result (content value: %s): %s"
        % (
            content,
            ", ".join(str(arg) for arg in args),
        )
    )
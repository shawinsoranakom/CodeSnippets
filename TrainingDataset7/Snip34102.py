def params_and_context_block(context, content, arg):
    """Expected params_and_context_block __doc__"""
    return (
        "params_and_context_block - Expected result (context value: %s) "
        "(content value: %s): %s"
        % (
            context["value"],
            content,
            arg,
        )
    )
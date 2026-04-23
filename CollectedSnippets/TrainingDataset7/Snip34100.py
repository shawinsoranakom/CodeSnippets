def no_params_with_context_block(context, content):
    """Expected no_params_with_context_block __doc__"""
    return (
        "no_params_with_context_block - Expected result (context value: %s) "
        "(content value: %s)" % (context["value"], content)
    )
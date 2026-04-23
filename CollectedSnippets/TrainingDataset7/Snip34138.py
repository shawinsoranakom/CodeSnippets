def inclusion_params_and_context(context, arg):
    """Expected inclusion_params_and_context __doc__"""
    return {
        "result": (
            "inclusion_params_and_context - Expected result (context value: %s): %s"
        )
        % (context["value"], arg)
    }
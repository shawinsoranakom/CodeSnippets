def inclusion_no_params_with_context_from_template(context):
    """Expected inclusion_no_params_with_context_from_template __doc__"""
    return {
        "result": (
            "inclusion_no_params_with_context_from_template - Expected result (context "
            "value: %s)"
        )
        % context["value"]
    }
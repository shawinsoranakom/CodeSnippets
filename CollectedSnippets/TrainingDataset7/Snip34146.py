def inclusion_unlimited_args_from_template(one, two="hi", *args):
    """Expected inclusion_unlimited_args_from_template __doc__"""
    return {
        "result": (
            "inclusion_unlimited_args_from_template - Expected result: %s"
            % (", ".join(str(arg) for arg in [one, two, *args]))
        )
    }
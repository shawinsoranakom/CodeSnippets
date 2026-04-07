def inclusion_only_unlimited_args_from_template(*args):
    """Expected inclusion_only_unlimited_args_from_template __doc__"""
    return {
        "result": "inclusion_only_unlimited_args_from_template - Expected result: %s"
        % (", ".join(str(arg) for arg in args))
    }
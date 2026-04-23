def inclusion_only_unlimited_args(*args):
    """Expected inclusion_only_unlimited_args __doc__"""
    return {
        "result": "inclusion_only_unlimited_args - Expected result: %s"
        % (", ".join(str(arg) for arg in args))
    }
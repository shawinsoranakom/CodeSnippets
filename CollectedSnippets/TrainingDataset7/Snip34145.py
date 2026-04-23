def inclusion_unlimited_args(one, two="hi", *args):
    """Expected inclusion_unlimited_args __doc__"""
    return {
        "result": (
            "inclusion_unlimited_args - Expected result: %s"
            % (", ".join(str(arg) for arg in [one, two, *args]))
        )
    }
def inclusion_one_default_from_template(one, two="hi"):
    """Expected inclusion_one_default_from_template __doc__"""
    return {
        "result": "inclusion_one_default_from_template - Expected result: %s, %s"
        % (one, two)
    }
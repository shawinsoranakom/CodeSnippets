def escape_naive(context):
    """A tag that doesn't even think about escaping issues"""
    return "Hello {}!".format(context["name"])
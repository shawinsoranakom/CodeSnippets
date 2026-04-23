def escape_naive_block(context, content):
    """A block tag that doesn't even think about escaping issues"""
    return "Hello {}: {}!".format(context["name"], content)
def escape_explicit_block(context, content):
    """A block tag that uses escape explicitly"""
    return escape("Hello {}: {}!".format(context["name"], content))
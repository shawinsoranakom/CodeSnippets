def escape_explicit(context):
    """A tag that uses escape explicitly"""
    return escape("Hello {}!".format(context["name"]))
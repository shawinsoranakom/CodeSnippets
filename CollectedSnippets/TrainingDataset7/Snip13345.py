def partial_func(parser, token):
    """
    Render a partial previously declared with the ``{% partialdef %}`` tag.

    Usage::

        {% partial partial_name %}
    """
    match token.split_contents():
        case "partial", partial_name:
            extra_data = parser.extra_data
            partial_mapping = DeferredSubDict(extra_data, "partials")
            return PartialNode(partial_name, partial_mapping=partial_mapping)
        case _:
            raise TemplateSyntaxError("'partial' tag requires a single argument")
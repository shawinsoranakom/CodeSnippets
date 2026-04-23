def do_filter(parser, token):
    """
    Filter the contents of the block through variable filters.

    Filters can also be piped through each other, and they can have
    arguments -- just like in variable syntax.

    Sample usage::

        {% filter force_escape|lower %}
            This text will be HTML-escaped, and will appear in lowercase.
        {% endfilter %}

    Note that the ``escape`` and ``safe`` filters are not acceptable arguments.
    Instead, use the ``autoescape`` tag to manage autoescaping for blocks of
    template code.
    """
    # token.split_contents() isn't useful here because this tag doesn't accept
    # variable as arguments.
    _, rest = token.contents.split(None, 1)
    filter_expr = parser.compile_filter("var|%s" % (rest))
    for func, unused in filter_expr.filters:
        filter_name = getattr(func, "_filter_name", None)
        if filter_name in ("escape", "safe"):
            raise TemplateSyntaxError(
                '"filter %s" is not permitted. Use the "autoescape" tag instead.'
                % filter_name
            )
    nodelist = parser.parse(("endfilter",))
    parser.delete_first_token()
    return FilterNode(filter_expr, nodelist)
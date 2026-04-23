def partialdef_func(parser, token):
    """
    Declare a partial that can be used in the template.

    Usage::

        {% partialdef partial_name %}
        Content goes here.
        {% endpartialdef %}

    Store the nodelist in the context under the key "partials". It can be
    retrieved using the ``{% partial %}`` tag.

    The optional ``inline`` argument renders the partial's contents
    immediately, at the point where it is defined.
    """
    match token.split_contents():
        case "partialdef", partial_name, "inline":
            inline = True
        case "partialdef", partial_name, _:
            raise TemplateSyntaxError(
                "The 'inline' argument does not have any parameters; either use "
                "'inline' or remove it completely."
            )
        case "partialdef", partial_name:
            inline = False
        case ["partialdef"]:
            raise TemplateSyntaxError("'partialdef' tag requires a name")
        case _:
            raise TemplateSyntaxError("'partialdef' tag takes at most 2 arguments")

    # Parse the content until the end tag.
    valid_endpartials = ("endpartialdef", f"endpartialdef {partial_name}")

    pos_open = getattr(token, "position", None)
    source_start = pos_open[0] if isinstance(pos_open, tuple) else None

    nodelist = parser.parse(valid_endpartials)
    endpartial = parser.next_token()
    if endpartial.contents not in valid_endpartials:
        parser.invalid_block_tag(endpartial, "endpartialdef", valid_endpartials)

    pos_close = getattr(endpartial, "position", None)
    source_end = pos_close[1] if isinstance(pos_close, tuple) else None

    # Store the partial nodelist in the parser.extra_data attribute.
    partials = parser.extra_data.setdefault("partials", {})
    if partial_name in partials:
        raise TemplateSyntaxError(
            f"Partial '{partial_name}' is already defined in the "
            f"'{parser.origin.name}' template."
        )
    partials[partial_name] = PartialTemplate(
        nodelist,
        parser.origin,
        partial_name,
        source_start=source_start,
        source_end=source_end,
    )

    return PartialDefNode(partial_name, inline, nodelist)
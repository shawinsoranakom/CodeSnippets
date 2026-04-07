def templatetag(parser, token):
    """
    Output one of the bits used to compose template tags.

    Since the template system has no concept of "escaping", to display one of
    the bits used in template tags, you must use the ``{% templatetag %}`` tag.

    The argument tells which template bit to output:

        ==================  =======
        Argument            Outputs
        ==================  =======
        ``openblock``       ``{%``
        ``closeblock``      ``%}``
        ``openvariable``    ``{{``
        ``closevariable``   ``}}``
        ``openbrace``       ``{``
        ``closebrace``      ``}``
        ``opencomment``     ``{#``
        ``closecomment``    ``#}``
        ==================  =======
    """
    # token.split_contents() isn't useful here because this tag doesn't accept
    # variable as arguments.
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError("'templatetag' statement takes one argument")
    tag = bits[1]
    if tag not in TemplateTagNode.mapping:
        raise TemplateSyntaxError(
            "Invalid templatetag argument: '%s'."
            " Must be one of: %s" % (tag, list(TemplateTagNode.mapping))
        )
    return TemplateTagNode(tag)
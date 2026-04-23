def language(parser, token):
    """
    Enable the given language just for this block.

    Usage::

        {% language "de" %}
            This is {{ bar }} and {{ boo }}.
        {% endlanguage %}
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument (language)" % bits[0])
    language = parser.compile_filter(bits[1])
    nodelist = parser.parse(("endlanguage",))
    parser.delete_first_token()
    return LanguageNode(nodelist, language)
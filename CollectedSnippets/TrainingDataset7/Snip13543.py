def do_get_available_languages(parser, token):
    """
    Store a list of available languages in the context.

    Usage::

        {% get_available_languages as languages %}
        {% for language in languages %}
        ...
        {% endfor %}

    This puts settings.LANGUAGES into the named variable.
    """
    # token.split_contents() isn't useful here because this tag doesn't accept
    # variable as arguments.
    args = token.contents.split()
    if len(args) != 3 or args[1] != "as":
        raise TemplateSyntaxError(
            "'get_available_languages' requires 'as variable' (got %r)" % args
        )
    return GetAvailableLanguagesNode(args[2])
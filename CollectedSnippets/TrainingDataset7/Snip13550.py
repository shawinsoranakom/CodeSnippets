def do_get_current_language(parser, token):
    """
    Store the current language in the context.

    Usage::

        {% get_current_language as language %}

    This fetches the currently active language and puts its value into the
    ``language`` context variable.
    """
    # token.split_contents() isn't useful here because this tag doesn't accept
    # variable as arguments.
    args = token.contents.split()
    if len(args) != 3 or args[1] != "as":
        raise TemplateSyntaxError(
            "'get_current_language' requires 'as variable' (got %r)" % args
        )
    return GetCurrentLanguageNode(args[2])
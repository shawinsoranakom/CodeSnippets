def do_get_current_language_bidi(parser, token):
    """
    Store the current language layout in the context.

    Usage::

        {% get_current_language_bidi as bidi %}

    This fetches the currently active language's layout and puts its value into
    the ``bidi`` context variable. True indicates right-to-left layout,
    otherwise left-to-right.
    """
    # token.split_contents() isn't useful here because this tag doesn't accept
    # variable as arguments.
    args = token.contents.split()
    if len(args) != 3 or args[1] != "as":
        raise TemplateSyntaxError(
            "'get_current_language_bidi' requires 'as variable' (got %r)" % args
        )
    return GetCurrentLanguageBidiNode(args[2])
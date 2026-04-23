def format_html_join(sep, format_string, args_generator):
    """
    A wrapper of format_html, for the common case of a group of arguments that
    need to be formatted using the same format string, and then joined using
    'sep'. 'sep' is also passed through conditional_escape.

    'args_generator' should be an iterator that returns the sequence of 'args'
    that will be passed to format_html.

    Example:

      format_html_join('\n', "<li>{} {}</li>", ((u.first_name, u.last_name)
                                                  for u in users))
    """
    return mark_safe(
        conditional_escape(sep).join(
            (
                format_html(format_string, **args)
                if isinstance(args, Mapping)
                else format_html(format_string, *args)
            )
            for args in args_generator
        )
    )
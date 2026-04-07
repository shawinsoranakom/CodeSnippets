def now(parser, token):
    """
    Display the date, formatted according to the given string.

    Use the same format as PHP's ``date()`` function; see https://php.net/date
    for all the possible values.

    Sample usage::

        It is {% now "jS F Y H:i" %}
    """
    bits = token.split_contents()
    asvar = None
    if len(bits) == 4 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]
    if len(bits) != 2:
        raise TemplateSyntaxError("'now' statement takes one argument")
    format_string = bits[1][1:-1]
    return NowNode(format_string, asvar)
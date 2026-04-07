def lorem(parser, token):
    """
    Create random Latin text useful for providing test data in templates.

    Usage format::

        {% lorem [count] [method] [random] %}

    ``count`` is a number (or variable) containing the number of paragraphs or
    words to generate (default is 1).

    ``method`` is either ``w`` for words, ``p`` for HTML paragraphs, ``b`` for
    plain-text paragraph blocks (default is ``b``).

    ``random`` is the word ``random``, which if given, does not use the common
    paragraph (starting "Lorem ipsum dolor sit amet, consectetuer...").

    Examples:

    * ``{% lorem %}`` outputs the common "lorem ipsum" paragraph
    * ``{% lorem 3 p %}`` outputs the common "lorem ipsum" paragraph
      and two random paragraphs each wrapped in HTML ``<p>`` tags
    * ``{% lorem 2 w random %}`` outputs two random latin words
    """
    bits = list(token.split_contents())
    tagname = bits[0]
    # Random bit
    common = bits[-1] != "random"
    if not common:
        bits.pop()
    # Method bit
    if bits[-1] in ("w", "p", "b"):
        method = bits.pop()
    else:
        method = "b"
    # Count bit
    if len(bits) > 1:
        count = bits.pop()
    else:
        count = "1"
    count = parser.compile_filter(count)
    if len(bits) != 1:
        raise TemplateSyntaxError("Incorrect format for %r tag" % tagname)
    return LoremNode(count, method, common)
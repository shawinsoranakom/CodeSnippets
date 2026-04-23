def parse_html(html):
    """
    Take a string that contains HTML and turn it into a Python object structure
    that can be easily compared against other HTML on semantic equivalence.
    Syntactical differences like which quotation is used on arguments will be
    ignored.
    """
    parser = Parser()
    parser.feed(html)
    parser.close()
    document = parser.root
    document.finalize()
    # Removing ROOT element if it's not necessary
    if len(document.children) == 1 and not isinstance(document.children[0], str):
        document = document.children[0]
    return document
def load(parser, token):
    """
    Load a custom template tag library into the parser.

    For example, to load the template tags in
    ``django/templatetags/news/photos.py``::

        {% load news.photos %}

    Can also be used to load an individual tag/filter from
    a library::

        {% load byline from news %}
    """
    # token.split_contents() isn't useful here because this tag doesn't accept
    # variable as arguments.
    bits = token.contents.split()
    if len(bits) >= 4 and bits[-2] == "from":
        # from syntax is used; load individual tags from the library
        name = bits[-1]
        lib = find_library(parser, name)
        subset = load_from_library(lib, name, bits[1:-2])
        parser.add_library(subset)
    else:
        # one or more libraries are specified; load and add them to the parser
        for name in bits[1:]:
            lib = find_library(parser, name)
            parser.add_library(lib)
    return LoadNode()
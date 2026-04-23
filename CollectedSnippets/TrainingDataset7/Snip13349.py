def spaceless(parser, token):
    """
    Remove whitespace between HTML tags, including tab and newline characters.

    Example usage::

        {% spaceless %}
            <p>
                <a href="foo/">Foo</a>
            </p>
        {% endspaceless %}

    This example returns this HTML::

        <p><a href="foo/">Foo</a></p>

    Only space between *tags* is normalized -- not space between tags and text.
    In this example, the space around ``Hello`` isn't stripped::

        {% spaceless %}
            <strong>
                Hello
            </strong>
        {% endspaceless %}
    """
    nodelist = parser.parse(("endspaceless",))
    parser.delete_first_token()
    return SpacelessNode(nodelist)
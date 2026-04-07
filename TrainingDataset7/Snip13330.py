def comment(parser, token):
    """
    Ignore everything between ``{% comment %}`` and ``{% endcomment %}``.
    """
    parser.skip_past("endcomment")
    return CommentNode()
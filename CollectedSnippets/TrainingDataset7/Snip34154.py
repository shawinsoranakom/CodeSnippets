def badtag(parser, token):
    parser.parse(("endbadtag",))
    parser.delete_first_token()
    return BadNode()
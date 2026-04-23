def do_extra_data(parser, token):
    parser.extra_data["extra_data"] = "CUSTOM_DATA"
    return TextNode("")
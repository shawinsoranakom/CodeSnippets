def find_library(parser, name):
    try:
        return parser.libraries[name]
    except KeyError:
        raise TemplateSyntaxError(
            "'%s' is not a registered tag library. Must be one of:\n%s"
            % (
                name,
                "\n".join(sorted(parser.libraries)),
            ),
        )
def handle_token(cls, parser, token):
        """
        Class method to parse prefix node and return a Node.
        """
        bits = token.split_contents()

        if len(bits) < 2:
            raise template.TemplateSyntaxError(
                "'%s' takes at least one argument (path to file)" % bits[0]
            )

        path = parser.compile_filter(bits[1])

        if len(bits) >= 2 and bits[-2] == "as":
            varname = bits[3]
        else:
            varname = None

        return cls(varname, path)
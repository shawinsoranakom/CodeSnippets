def handle_token(cls, parser, token, name):
        """
        Class method to parse prefix node and return a Node.
        """
        # token.split_contents() isn't useful here because tags using this
        # method don't accept variable as arguments.
        tokens = token.contents.split()
        if len(tokens) > 1 and tokens[1] != "as":
            raise template.TemplateSyntaxError(
                "First argument in '%s' must be 'as'" % tokens[0]
            )
        if len(tokens) > 1:
            varname = tokens[2]
        else:
            varname = None
        return cls(varname, name)
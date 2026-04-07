def __init__(self, token_type, contents, position=None, lineno=None):
        """
        A token representing a string from the template.

        token_type
            A TokenType, either .TEXT, .VAR, .BLOCK, or .COMMENT.

        contents
            The token source string.

        position
            An optional tuple containing the start and end index of the token
            in the template source. This is used for traceback information
            when debug is on.

        lineno
            The line number the token appears on in the template source.
            This is used for traceback information and gettext files.
        """
        self.token_type = token_type
        self.contents = contents
        self.lineno = lineno
        self.position = position
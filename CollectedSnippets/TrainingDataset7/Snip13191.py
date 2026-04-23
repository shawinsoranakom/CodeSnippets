def error(self, token, e):
        """
        Return an exception annotated with the originating token. Since the
        parser can be called recursively, check if a token is already set. This
        ensures the innermost token is highlighted if an exception occurs,
        e.g. a compile error within the body of an if statement.
        """
        if not isinstance(e, Exception):
            e = TemplateSyntaxError(e)
        if not hasattr(e, "token"):
            e.token = token
        return e
def render_token_list(self, tokens):
        result = []
        vars = []
        for token in tokens:
            if token.token_type == TokenType.TEXT:
                result.append(token.contents.replace("%", "%%"))
            elif token.token_type == TokenType.VAR:
                result.append("%%(%s)s" % token.contents)
                vars.append(token.contents)
        msg = "".join(result)
        if self.trimmed:
            msg = translation.trim_whitespace(msg)
        return msg, vars
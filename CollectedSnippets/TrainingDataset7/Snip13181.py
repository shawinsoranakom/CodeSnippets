def tokenize(self):
        """
        Return a list of tokens from a given template_string.
        """
        in_tag = False
        lineno = 1
        result = []
        for token_string in tag_re.split(self.template_string):
            if token_string:
                result.append(self.create_token(token_string, None, lineno, in_tag))
                lineno += token_string.count("\n")
            in_tag = not in_tag
        return result
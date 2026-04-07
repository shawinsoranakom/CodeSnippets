def _get_token_line_number(self, path, token):
        with open(path) as f:
            for line, content in enumerate(f, 1):
                if token in content:
                    return line
        self.fail(
            "The token '%s' could not be found in %s, please check the test config"
            % (token, path)
        )
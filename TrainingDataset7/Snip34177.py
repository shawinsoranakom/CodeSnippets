def make_expected(self):
        # The non-debug lexer does not record position.
        return [t[:-1] + (None,) for t in self.expected_token_tuples]
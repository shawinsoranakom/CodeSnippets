def test_tokenize(self):
        tokens = self.lexer_class(self.template_string).tokenize()
        token_tuples = [
            (t.token_type, t.contents, t.lineno, t.position) for t in tokens
        ]
        self.assertEqual(token_tuples, self.make_expected())
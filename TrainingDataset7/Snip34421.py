def test_repr(self):
        token = Token(TokenType.BLOCK, "some text")
        self.assertEqual(repr(token), '<Block token: "some text...">')
        parser = Parser([token], builtins=[filter_library])
        self.assertEqual(
            repr(parser),
            '<Parser tokens=[<Block token: "some text...">]>',
        )
        filter_expression = FilterExpression("news|upper", parser)
        self.assertEqual(repr(filter_expression), "<FilterExpression 'news|upper'>")
        lexer = Lexer("{% for i in 1 %}{{ a }}\n{% endfor %}")
        self.assertEqual(
            repr(lexer),
            '<Lexer template_string="{% for i in 1 %}{{ a...", verbatim=False>',
        )
def test_repr(self):
        block_translate_node = BlockTranslateNode(
            extra_context={},
            singular=[
                Token(TokenType.TEXT, "content"),
                Token(TokenType.VAR, "variable"),
            ],
        )
        self.assertEqual(
            repr(block_translate_node),
            "<BlockTranslateNode: extra_context={} "
            'singular=[<Text token: "content...">, <Var token: "variable...">] '
            "plural=None>",
        )
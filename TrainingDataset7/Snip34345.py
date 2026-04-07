def test_tag_parens(self):
        @self.library.tag()
        def func(parser, token):
            return Node()

        self.assertEqual(self.library.tags["func"], func)
def test_simple_block_tag_parens(self):
        @self.library.simple_block_tag()
        def func(content):
            return content

        self.assertIn("func", self.library.tags)
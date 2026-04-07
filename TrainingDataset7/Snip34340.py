def test_simple_block_tag_deferred_annotation(self):
        @self.library.simple_block_tag
        def func(content: SomeType):  # NOQA: F821
            return content

        self.assertIn("func", self.library.tags)
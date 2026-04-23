def test_tag_deferred_annotation(self):
        @self.library.simple_tag
        def func(parser, token: SomeType):  # NOQA: F821
            return Node()

        self.assertIn("func", self.library.tags)
def test_simple_block_tag_name_kwarg(self):
        @self.library.simple_block_tag(name="name")
        def func(content):
            return content

        self.assertIn("name", self.library.tags)
def test_simple_tag(self):
        @self.library.simple_tag
        def func():
            return ""

        self.assertIn("func", self.library.tags)
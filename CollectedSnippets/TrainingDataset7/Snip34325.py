def test_inclusion_tag(self):
        @self.library.inclusion_tag("template.html")
        def func():
            return ""

        self.assertIn("func", self.library.tags)
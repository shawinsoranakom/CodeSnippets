def test_inclusion_tag_name(self):
        @self.library.inclusion_tag("template.html", name="name")
        def func():
            return ""

        self.assertIn("name", self.library.tags)
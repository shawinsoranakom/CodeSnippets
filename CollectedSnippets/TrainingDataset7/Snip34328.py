def test_inclusion_tag_deferred_annotation(self):
        @self.library.inclusion_tag("template.html")
        def func(arg: SomeType):  # NOQA: F821
            return ""

        self.assertIn("func", self.library.tags)
def test_autoescape_filtertag01(self):
        """
        The "safe" and "escape" filters cannot work due to internal
        implementation details (fortunately, the (no)autoescape block
        tags can be used in those cases)
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("autoescape-filtertag01", {"first": "<a>"})
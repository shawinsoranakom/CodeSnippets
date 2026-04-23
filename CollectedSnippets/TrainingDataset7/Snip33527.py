def test_exception02(self):
        """
        Raise exception for invalid variable template name
        """
        if self.engine.string_if_invalid:
            with self.assertRaises(TemplateDoesNotExist):
                self.engine.render_to_string("exception02")
        else:
            with self.assertRaises(TemplateSyntaxError):
                self.engine.render_to_string("exception02")
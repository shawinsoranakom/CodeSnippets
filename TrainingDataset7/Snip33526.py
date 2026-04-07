def test_exception01(self):
        """
        Raise exception for invalid template name
        """
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.render_to_string("exception01")
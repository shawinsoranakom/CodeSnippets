def test_exception05(self):
        """
        Raise exception for block.super used in base template
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("exception05")
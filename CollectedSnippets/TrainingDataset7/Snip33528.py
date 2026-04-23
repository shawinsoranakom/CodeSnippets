def test_exception03(self):
        """
        Raise exception for extra {% extends %} tags
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("exception03")
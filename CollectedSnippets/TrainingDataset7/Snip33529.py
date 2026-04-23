def test_exception04(self):
        """
        Raise exception for custom tags used in child with {% load %} tag in
        parent, not in child
        """
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("exception04")
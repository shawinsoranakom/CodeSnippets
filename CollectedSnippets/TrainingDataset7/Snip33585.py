def test_filter_syntax08(self):
        """
        Raise TemplateSyntaxError for empty block tags
        """
        with self.assertRaisesMessage(TemplateSyntaxError, "Empty block tag on line 1"):
            self.engine.get_template("filter-syntax08")
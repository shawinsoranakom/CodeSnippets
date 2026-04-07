def test_filter_syntax08_multi_line(self):
        """
        Raise TemplateSyntaxError for empty block tags in templates with
        multiple lines.
        """
        with self.assertRaisesMessage(TemplateSyntaxError, "Empty block tag on line 3"):
            self.engine.get_template("filter-syntax08-multi-line")
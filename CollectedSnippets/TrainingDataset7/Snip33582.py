def test_filter_syntax05(self):
        """
        Raise TemplateSyntaxError for a nonexistent filter
        """
        msg = "Invalid filter: 'does_not_exist'"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("filter-syntax05")
def test_filter_syntax07(self):
        """
        Raise TemplateSyntaxError for invalid block tags
        """
        msg = (
            "Invalid block tag on line 1: 'nothing_to_see_here'. Did you "
            "forget to register or load this tag?"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("filter-syntax07")
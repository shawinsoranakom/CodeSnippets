def test_filter_syntax06(self):
        """
        Raise TemplateSyntaxError when trying to access a filter containing
        an illegal character
        """
        with self.assertRaisesMessage(TemplateSyntaxError, "Invalid filter: 'fil'"):
            self.engine.get_template("filter-syntax06")
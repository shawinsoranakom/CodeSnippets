def test_compile_filter_expression_error(self):
        """
        19819 -- Make sure the correct token is highlighted for
        FilterExpression errors.
        """
        engine = self._engine()
        msg = "Could not parse the remainder: '@bar' from 'foo@bar'"

        with self.assertRaisesMessage(TemplateSyntaxError, msg) as e:
            engine.from_string("{% if 1 %}{{ foo@bar }}{% endif %}")

        if self.debug_engine:
            debug = e.exception.template_debug
            self.assertEqual((debug["start"], debug["end"]), (10, 23))
            self.assertEqual((debug["during"]), "{{ foo@bar }}")
def test_cannot_find_variable(self):
        p = Parser("", builtins=[filter_library])
        with self.assertRaisesMessage(
            TemplateSyntaxError,
            'Could not find variable at start of |default:"Default"',
        ):
            FilterExpression('|default:"Default"', p)
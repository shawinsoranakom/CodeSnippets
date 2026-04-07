def test_variable_parsing(self):
        c = {"article": {"section": "News"}}
        self.assertEqual(Variable("article.section").resolve(c), "News")
        self.assertEqual(Variable('"News"').resolve(c), "News")
        self.assertEqual(Variable("'News'").resolve(c), "News")

        # Translated strings are handled correctly.
        self.assertEqual(Variable("_(article.section)").resolve(c), "News")
        self.assertEqual(Variable('_("Good News")').resolve(c), "Good News")
        self.assertEqual(Variable("_('Better News')").resolve(c), "Better News")

        # Escaped quotes work correctly as well.
        self.assertEqual(
            Variable(r'"Some \"Good\" News"').resolve(c), 'Some "Good" News'
        )
        self.assertEqual(
            Variable(r"'Some \'Better\' News'").resolve(c), "Some 'Better' News"
        )

        # Variables should reject access of attributes and variables beginning
        # with underscores.
        for name in ["article._hidden", "_article"]:
            msg = f"Variables and attributes may not begin with underscores: '{name}'"
            with self.assertRaisesMessage(TemplateSyntaxError, msg):
                Variable(name)

        # Variables should raise on non string type
        with self.assertRaisesMessage(
            TypeError, "Variable must be a string or number, got <class 'dict'>"
        ):
            Variable({})

        # Variables should raise when invalid characters in name.
        for c in ["+", "-"]:
            with self.subTest(invalid_character=c):
                variable_name = f"variable{c}name"
                with self.assertRaisesMessage(
                    TemplateSyntaxError,
                    f"Invalid character ('{c}') in variable name: '{variable_name}'",
                ):
                    Variable(variable_name)
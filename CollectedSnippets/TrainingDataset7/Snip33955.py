def test_resetcycle04(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "Named cycle 'undefinedcycle' does not exist."
        ):
            self.engine.get_template("resetcycle04")
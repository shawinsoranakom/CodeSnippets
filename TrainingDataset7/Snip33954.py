def test_resetcycle03(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "Named cycle 'undefinedcycle' does not exist."
        ):
            self.engine.get_template("resetcycle03")
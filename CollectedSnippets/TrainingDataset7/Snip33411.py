def test_basic_syntax07(self):
        """
        Raise TemplateSyntaxError for empty variable tags.
        """
        with self.assertRaisesMessage(
            TemplateSyntaxError, "Empty variable tag on line 1"
        ):
            self.engine.get_template("basic-syntax07")
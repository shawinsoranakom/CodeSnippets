def test_include_empty(self):
        msg = (
            "'include' tag takes at least one argument: the name of the "
            "template to be included."
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("include_empty")
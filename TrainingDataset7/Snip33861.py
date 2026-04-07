def test_load09(self):
        msg = (
            "'from' is not a registered tag library. Must be one of:\n"
            "subpackage.echo\ntesttags"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("load09")
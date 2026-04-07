def test_load08(self):
        msg = (
            "'echo' is not a registered tag library. Must be one of:\n"
            "subpackage.echo\ntesttags"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("load08")
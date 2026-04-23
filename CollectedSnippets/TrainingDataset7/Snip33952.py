def test_resetcycle01(self):
        with self.assertRaisesMessage(TemplateSyntaxError, "No cycles in template."):
            self.engine.get_template("resetcycle01")
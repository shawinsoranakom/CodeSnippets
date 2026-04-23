def test_cycle05(self):
        msg = "'cycle' tag requires at least two arguments"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("cycle05")
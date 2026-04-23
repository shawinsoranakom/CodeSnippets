def test_cycle18(self):
        msg = "Only 'silent' flag is allowed after cycle's name, not 'invalid_flag'."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("cycle18")
def test_regroup07(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("regroup07")
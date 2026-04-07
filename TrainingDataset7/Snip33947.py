def test_regroup05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("regroup05")
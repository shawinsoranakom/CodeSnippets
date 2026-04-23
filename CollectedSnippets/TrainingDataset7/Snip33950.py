def test_regroup08(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("regroup08")
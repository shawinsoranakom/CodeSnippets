def test_regroup06(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("regroup06")
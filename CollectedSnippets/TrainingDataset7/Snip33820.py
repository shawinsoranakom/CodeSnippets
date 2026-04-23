def test_include_fail1(self):
        with self.assertRaises(RuntimeError):
            self.engine.get_template("include-fail1")
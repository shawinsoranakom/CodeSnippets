def test_include_error07(self):
        template = self.engine.get_template("include-error07")
        with self.assertRaises(RuntimeError):
            template.render(Context())
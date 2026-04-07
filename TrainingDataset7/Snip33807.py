def test_include08(self):
        output = self.engine.render_to_string(
            "include08", {"headline": "basic-syntax02"}
        )
        self.assertEqual(output, "Dynamic")
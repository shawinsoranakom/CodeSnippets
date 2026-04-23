def test_length01(self):
        output = self.engine.render_to_string(
            "length01", {"list": ["4", None, True, {}]}
        )
        self.assertEqual(output, "4")
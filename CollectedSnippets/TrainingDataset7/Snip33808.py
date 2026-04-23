def test_include09(self):
        output = self.engine.render_to_string(
            "include09", {"first": "Ul", "second": "lU"}
        )
        self.assertEqual(output, "Ul--LU --- UL--lU")
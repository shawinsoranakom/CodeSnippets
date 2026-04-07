def test_forloop_length(self):
        cases = [
            ([1, 2, 3], "333"),
            ([1, 2, 3, 4, 5, 6], "666666"),
            ([], ""),
        ]
        for values, expected_output in cases:
            for template in ["forloop-length", "forloop-length-reversed"]:
                with self.subTest(expected_output=expected_output, template=template):
                    output = self.engine.render_to_string(template, {"values": values})
                    self.assertEqual(output, expected_output)
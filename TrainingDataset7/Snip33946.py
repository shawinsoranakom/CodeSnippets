def test_regroup04(self):
        """
        The join template filter has needs_autoescape = True
        """
        output = self.engine.render_to_string(
            "regroup04",
            {
                "data": [
                    {"foo": "x", "bar": ["ab", "c"]},
                    {"foo": "y", "bar": ["a", "bc"]},
                    {"foo": "z", "bar": ["a", "d"]},
                ],
            },
        )
        self.assertEqual(output, "abc:xy,ad:z,")
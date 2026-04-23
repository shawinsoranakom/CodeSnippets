def test_regroup01(self):
        output = self.engine.render_to_string(
            "regroup01",
            {
                "data": [
                    {"foo": "c", "bar": 1},
                    {"foo": "d", "bar": 1},
                    {"foo": "a", "bar": 2},
                    {"foo": "b", "bar": 2},
                    {"foo": "x", "bar": 3},
                ],
            },
        )
        self.assertEqual(output, "1:cd,2:ab,3:x,")
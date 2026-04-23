def test_regroup_unpack(self):
        output = self.engine.render_to_string(
            "regroup_unpack",
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
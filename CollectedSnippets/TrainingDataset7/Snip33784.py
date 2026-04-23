def test_ifchanged08(self):
        output = self.engine.render_to_string(
            "ifchanged08",
            {
                "datalist": [
                    [(1, "a"), (1, "a"), (0, "b"), (1, "c")],
                    [(0, "a"), (1, "c"), (1, "d"), (1, "d"), (0, "e")],
                ]
            },
        )
        self.assertEqual(output, "accd")
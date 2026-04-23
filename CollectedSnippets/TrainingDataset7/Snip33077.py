def test_striptags01(self):
        output = self.engine.render_to_string(
            "striptags01",
            {
                "a": "<a>x</a> <p><b>y</b></p>",
                "b": mark_safe("<a>x</a> <p><b>y</b></p>"),
            },
        )
        self.assertEqual(output, "x y x y")
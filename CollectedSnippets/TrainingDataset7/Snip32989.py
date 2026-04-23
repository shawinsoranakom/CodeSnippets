def test_linebreaks02(self):
        output = self.engine.render_to_string(
            "linebreaks02", {"a": "x&\ny", "b": mark_safe("x&\ny")}
        )
        self.assertEqual(output, "<p>x&<br>y</p> <p>x&<br>y</p>")
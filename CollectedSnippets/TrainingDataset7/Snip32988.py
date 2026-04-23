def test_linebreaks01(self):
        output = self.engine.render_to_string(
            "linebreaks01", {"a": "x&\ny", "b": mark_safe("x&\ny")}
        )
        self.assertEqual(output, "<p>x&amp;<br>y</p> <p>x&<br>y</p>")
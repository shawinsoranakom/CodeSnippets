def test_linebreaksbr01(self):
        output = self.engine.render_to_string(
            "linebreaksbr01", {"a": "x&\ny", "b": mark_safe("x&\ny")}
        )
        self.assertEqual(output, "x&amp;<br>y x&<br>y")
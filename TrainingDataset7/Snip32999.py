def test_linebreaksbr02(self):
        output = self.engine.render_to_string(
            "linebreaksbr02", {"a": "x&\ny", "b": mark_safe("x&\ny")}
        )
        self.assertEqual(output, "x&<br>y x&<br>y")
def test_basic(self):
        output = self.engine.render_to_string(
            "escapeseq_basic",
            {"a": ["x&y", "<p>"], "b": [mark_safe("x&y"), mark_safe("<p>")]},
        )
        self.assertEqual(output, "x&amp;y, &lt;p&gt; -- x&y, <p>")
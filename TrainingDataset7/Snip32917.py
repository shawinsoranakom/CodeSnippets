def test_chain_join_autoescape_off(self):
        output = self.engine.render_to_string(
            "escapeseq_join_autoescape_off", {"a": ["x&y", "<p>"]}
        )
        self.assertEqual(output, "x&amp;y<br/>&lt;p&gt;")
def test_chain_join(self):
        output = self.engine.render_to_string("escapeseq_join", {"a": ["x&y", "<p>"]})
        self.assertEqual(output, "x&amp;y<br/>&lt;p&gt;")
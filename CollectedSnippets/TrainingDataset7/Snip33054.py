def test_safeseq01(self):
        output = self.engine.render_to_string("safeseq01", {"a": ["&", "<"]})
        self.assertEqual(output, "&amp;, &lt; -- &, <")
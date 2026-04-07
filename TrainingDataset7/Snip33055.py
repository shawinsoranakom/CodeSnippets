def test_safeseq02(self):
        output = self.engine.render_to_string("safeseq02", {"a": ["&", "<"]})
        self.assertEqual(output, "&, < -- &, <")
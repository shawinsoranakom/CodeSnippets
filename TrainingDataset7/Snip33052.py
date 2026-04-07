def test_safe01(self):
        output = self.engine.render_to_string("safe01", {"a": "<b>hello</b>"})
        self.assertEqual(output, "&lt;b&gt;hello&lt;/b&gt; -- <b>hello</b>")
def test_join_autoescape_off(self):
        var_list = ["<p>Hello World!</p>", "beta & me", "<script>Hi!</script>"]
        context = {"var_list": var_list, "var_joiner": "<br/>"}
        output = self.engine.render_to_string("join_autoescape_off", context)
        expected_result = "<p>Hello World!</p><br/>beta & me<br/><script>Hi!</script>"
        self.assertEqual(output, expected_result)
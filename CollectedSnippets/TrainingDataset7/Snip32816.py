def test_addslashes02(self):
        output = self.engine.render_to_string(
            "addslashes02", {"a": "<a>'", "b": mark_safe("<a>'")}
        )
        self.assertEqual(output, r"&lt;a&gt;\&#x27; <a>\'")
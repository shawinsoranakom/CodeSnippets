def test_basic_context(self):
        self.assertEqual(
            self.engine.render_to_string("test_context.html", {"obj": "test"}),
            "obj:test\n",
        )
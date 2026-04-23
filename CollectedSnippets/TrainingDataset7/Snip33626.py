def test_firstof15(self):
        ctx = {"a": 0, "b": 2, "c": 3}
        output = self.engine.render_to_string("firstof15", ctx)
        self.assertEqual(ctx["myvar"], "2")
        self.assertEqual(output, "")
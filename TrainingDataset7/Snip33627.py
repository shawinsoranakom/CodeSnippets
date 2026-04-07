def test_all_false_arguments_asvar(self):
        ctx = {"a": 0, "b": 0, "c": 0}
        output = self.engine.render_to_string("firstof16", ctx)
        self.assertEqual(ctx["myvar"], "")
        self.assertEqual(output, "")
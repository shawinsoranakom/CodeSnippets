def test_firstof03(self):
        output = self.engine.render_to_string("firstof03", {"a": 0, "c": 0, "b": 2})
        self.assertEqual(output, "2")
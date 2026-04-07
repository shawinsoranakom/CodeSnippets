def test_add03(self):
        output = self.engine.render_to_string("add03", {"i": "not_an_int"})
        self.assertEqual(output, "")
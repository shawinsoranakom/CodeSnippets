def test_include12(self):
        output = self.engine.render_to_string("include12", {"second": "2"})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "1 --- INVALID")
        else:
            self.assertEqual(output, "1 --- ")
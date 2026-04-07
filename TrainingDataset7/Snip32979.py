def test_length02(self):
        output = self.engine.render_to_string("length02", {"list": []})
        self.assertEqual(output, "0")
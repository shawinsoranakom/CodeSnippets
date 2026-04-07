def test_true(self):
        output = self.engine.render_to_string("t", {"var": True})
        self.assertEqual(output, "yup yes")
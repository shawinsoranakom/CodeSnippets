def test_load05(self):
        output = self.engine.render_to_string("load05", {"statement": "not shouting"})
        self.assertEqual(output, "this that theother NOT SHOUTING")
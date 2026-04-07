def test_load03(self):
        output = self.engine.render_to_string("load03")
        self.assertEqual(output, "this that theother")
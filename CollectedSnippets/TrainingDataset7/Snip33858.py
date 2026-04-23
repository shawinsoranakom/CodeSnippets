def test_load06(self):
        output = self.engine.render_to_string("load06")
        self.assertEqual(output, "test")
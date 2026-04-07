def test_namedendblocks01(self):
        output = self.engine.render_to_string("namedendblocks01")
        self.assertEqual(output, "1_2_3")
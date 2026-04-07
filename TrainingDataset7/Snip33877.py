def test_namedendblocks07(self):
        output = self.engine.render_to_string("namedendblocks07")
        self.assertEqual(output, "1_2_3")
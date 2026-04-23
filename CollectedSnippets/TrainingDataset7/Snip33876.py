def test_namedendblocks06(self):
        """
        Mixed named and unnamed endblocks
        """
        output = self.engine.render_to_string("namedendblocks06")
        self.assertEqual(output, "1_2_3")
def test_inheritance08(self):
        """
        Three-level with one block defined on this level, two blocks
        defined next level
        """
        output = self.engine.render_to_string("inheritance08")
        self.assertEqual(output, "1235")
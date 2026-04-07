def test_inheritance12(self):
        """
        Three-level with this level providing one and second level
        providing the other
        """
        output = self.engine.render_to_string("inheritance12")
        self.assertEqual(output, "1235")
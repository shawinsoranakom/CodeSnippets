def test_cache18(self):
        """
        Test whitespace in filter arguments
        """
        output = self.engine.render_to_string("cache18")
        self.assertEqual(output, "cache18")
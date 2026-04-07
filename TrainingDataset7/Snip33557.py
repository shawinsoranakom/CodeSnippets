def test_inheritance26(self):
        """
        Set up a base template to extend
        """
        output = self.engine.render_to_string("inheritance26")
        self.assertEqual(output, "no tags")
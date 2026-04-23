def test_inheritance19(self):
        """
        {% load %} tag (within a child template)
        """
        output = self.engine.render_to_string("inheritance19")
        self.assertEqual(output, "140056783_")
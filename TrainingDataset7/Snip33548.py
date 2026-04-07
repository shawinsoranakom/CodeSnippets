def test_inheritance17(self):
        """
        {% load %} tag (parent -- setup for exception04)
        """
        output = self.engine.render_to_string("inheritance17")
        self.assertEqual(output, "1234")
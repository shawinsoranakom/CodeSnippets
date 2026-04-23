def test_inheritance18(self):
        """
        {% load %} tag (standard usage, without inheritance)
        """
        output = self.engine.render_to_string("inheritance18")
        self.assertEqual(output, "this that theother5678")
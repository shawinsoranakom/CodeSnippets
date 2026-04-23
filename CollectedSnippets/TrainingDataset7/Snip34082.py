def test_with03(self):
        output = self.engine.render_to_string("with03", {"alpha": "A", "beta": "B"})
        self.assertEqual(output, "AB")
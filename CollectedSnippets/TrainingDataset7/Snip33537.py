def test_inheritance06(self):
        """
        Three-level with variable parent-template name
        """
        output = self.engine.render_to_string("inheritance06", {"foo": "inheritance02"})
        self.assertEqual(output, "1234")
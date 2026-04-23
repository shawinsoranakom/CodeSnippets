def test_numpy_array_index02(self):
        """
        Fail silently when the array index is out of range.
        """
        output = self.engine.render_to_string(
            "numpy-array-index02",
            {"var": numpy.array(["first item", "second item"])},
        )
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")
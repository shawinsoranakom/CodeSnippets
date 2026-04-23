def test_numpy_array_index01(self):
        """
        Numpy's array-index syntax allows a template to access a certain
        item of a subscriptable object.
        """
        output = self.engine.render_to_string(
            "numpy-array-index01",
            {"var": numpy.array(["first item", "second item"])},
        )
        self.assertEqual(output, "second item")
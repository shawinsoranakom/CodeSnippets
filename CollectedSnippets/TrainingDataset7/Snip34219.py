def test_context_comparable(self):
        """
        #21765 -- equality comparison should work
        """

        test_data = {"x": "y", "v": "z", "d": {"o": object, "a": "b"}}

        self.assertEqual(Context(test_data), Context(test_data))

        a = Context()
        b = Context()
        self.assertEqual(a, b)

        # update only a
        a.update({"a": 1})
        self.assertNotEqual(a, b)

        # update both to check regression
        a.update({"c": 3})
        b.update({"c": 3})
        self.assertNotEqual(a, b)

        # make contexts equals again
        b.update({"a": 1})
        self.assertEqual(a, b)
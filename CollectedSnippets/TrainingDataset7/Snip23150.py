def test_flatatt_no_side_effects(self):
        """
        flatatt() does not modify the dict passed in.
        """
        attrs = {"foo": "bar", "true": True, "false": False}
        attrs_copy = copy.copy(attrs)
        self.assertEqual(attrs, attrs_copy)

        first_run = flatatt(attrs)
        self.assertEqual(attrs, attrs_copy)
        self.assertEqual(first_run, ' foo="bar" true')

        second_run = flatatt(attrs)
        self.assertEqual(attrs, attrs_copy)

        self.assertEqual(first_run, second_run)
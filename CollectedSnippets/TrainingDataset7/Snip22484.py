def test_charfield_length_not_int(self):
        """
        Setting min_length or max_length to something that is not a number
        raises an exception.
        """
        with self.assertRaises(ValueError):
            CharField(min_length="a")
        with self.assertRaises(ValueError):
            CharField(max_length="a")
        msg = "__init__() takes 1 positional argument but 2 were given"
        with self.assertRaisesMessage(TypeError, msg):
            CharField("a")
def test_force_str_exception(self):
        """
        Broken __str__ actually raises an error.
        """

        class MyString:
            def __str__(self):
                return b"\xc3\xb6\xc3\xa4\xc3\xbc"

        # str(s) raises a TypeError if the result is not a text type.
        with self.assertRaises(TypeError):
            force_str(MyString())
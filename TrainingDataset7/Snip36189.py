def test_update_raises_correct_exceptions(self):
        # MultiValueDict.update() raises equivalent exceptions to
        # dict.update().
        # Non-iterable values raise TypeError.
        for value in [None, True, False, 123, 123.45]:
            with self.subTest(value), self.assertRaises(TypeError):
                MultiValueDict().update(value)
        # Iterables of objects that cannot be unpacked raise TypeError.
        for value in [b"123", b"abc", (1, 2, 3), [1, 2, 3], {1, 2, 3}]:
            with self.subTest(value), self.assertRaises(TypeError):
                MultiValueDict().update(value)
        # Iterables of unpackable objects with incorrect number of items raise
        # ValueError.
        for value in ["123", "abc", ("a", "b", "c"), ["a", "b", "c"], {"a", "b", "c"}]:
            with self.subTest(value), self.assertRaises(ValueError):
                MultiValueDict().update(value)
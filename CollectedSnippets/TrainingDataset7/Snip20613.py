def test_pad(self):
        Author.objects.create(name="John", alias="j")
        none_value = (
            "" if connection.features.interprets_empty_strings_as_nulls else None
        )
        tests = (
            (LPad("name", 7, Value("xy")), "xyxJohn"),
            (RPad("name", 7, Value("xy")), "Johnxyx"),
            (LPad("name", 6, Value("x")), "xxJohn"),
            (RPad("name", 6, Value("x")), "Johnxx"),
            # The default pad string is a space.
            (LPad("name", 6), "  John"),
            (RPad("name", 6), "John  "),
            # If string is longer than length it is truncated.
            (LPad("name", 2), "Jo"),
            (RPad("name", 2), "Jo"),
            (LPad("name", 0), ""),
            (RPad("name", 0), ""),
            (LPad("name", None), none_value),
            (RPad("name", None), none_value),
            (LPad(Value(None), 1), none_value),
            (RPad(Value(None), 1), none_value),
            (LPad("goes_by", 1), none_value),
            (RPad("goes_by", 1), none_value),
        )
        for function, padded_name in tests:
            with self.subTest(function=function):
                authors = Author.objects.annotate(padded_name=function)
                self.assertQuerySetEqual(
                    authors, [padded_name], lambda a: a.padded_name, ordered=False
                )
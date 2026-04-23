def make_is_type_mock(true_type_matchers):
    """Return a function that mocks is_type.

    When you do this:
    mock_is_type.side_effect = make_is_type_mock("foo.bar.Baz")

    ...then when you call mock_is_type(my_type, "foo.bar.Baz") it will return
    True (and False otherwise).

    You can also pass in a tuple.
    """
    if type(true_type_matchers) is not tuple:
        true_type_matchers = (true_type_matchers,)

    def new_is_type(obj, type_matchers):
        if type(type_matchers) is not tuple:
            type_matchers = (type_matchers,)

        for type_matcher in type_matchers:
            if type_matcher in true_type_matchers:
                return True
        return False

    return new_is_type
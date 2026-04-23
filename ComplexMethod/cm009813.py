def test_comma_list_with_iterables() -> None:
    """Test `comma_list` works with various iterable types."""
    # Tuple
    assert comma_list((1, 2, 3)) == "1, 2, 3"

    # Generator
    assert comma_list(x for x in range(3)) == "0, 1, 2"

    # Range
    assert comma_list(range(3)) == "0, 1, 2"

    # Empty iterable
    assert comma_list([]) == ""
    assert comma_list(()) == ""

    # Single item
    assert comma_list([1]) == "1"
    assert comma_list(("single",)) == "single"

    # Mixed types
    assert comma_list([1, "two", 3.0]) == "1, two, 3.0"
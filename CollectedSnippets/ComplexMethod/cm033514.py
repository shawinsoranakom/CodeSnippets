def assert_lists_contain_same_elements(a, b) -> None:
    """Assert that the two values given are lists that contain the same elements, even when the elements cannot be sorted or hashed."""
    assert isinstance(a, list)
    assert isinstance(b, list)

    missing_from_a = [item for item in b if item not in a]
    missing_from_b = [item for item in a if item not in b]

    assert not missing_from_a, f'elements from `b` {missing_from_a} missing from `a` {a}'
    assert not missing_from_b, f'elements from `a` {missing_from_b} missing from `b` {b}'
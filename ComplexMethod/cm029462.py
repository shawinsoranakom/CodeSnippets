def assert_structure_match(actual: object, expected: object, path: str = "") -> None:
    """
    Compare actual and expected structures with special markers:
    - <ANY>: Matches any value
    - <CONTAINS:text>: Checks if the actual value contains 'text'

    Args:
        actual: The actual value to check
        expected: The expected value or pattern
        path: Current path in the structure (for error messages)
    """
    if (
        isinstance(expected, str)
        and expected.startswith("<")
        and expected.endswith(">")
    ):
        # Handle special markers
        if expected == "<ANY>":
            # Match any value
            return
        elif expected.startswith("<CONTAINS:") and expected.endswith(">"):
            # Extract the text to search for
            search_text = expected[10:-1]  # Remove "<CONTAINS:" and ">"
            assert isinstance(
                actual, str
            ), f"At {path}: expected string, got {type(actual).__name__}"
            assert (
                search_text in actual
            ), f"At {path}: '{search_text}' not found in '{actual}'"
            return

    # Handle different types
    if isinstance(expected, dict):
        assert isinstance(
            actual, dict
        ), f"At {path}: expected dict, got {type(actual).__name__}"
        expected_dict: Dict[str, object] = expected
        actual_dict: Dict[str, object] = actual
        for key, value in expected_dict.items():
            assert key in actual_dict, f"At {path}: key '{key}' not found in actual"
            assert_structure_match(actual_dict[key], value, f"{path}.{key}" if path else key)
    elif isinstance(expected, list):
        assert isinstance(
            actual, list
        ), f"At {path}: expected list, got {type(actual).__name__}"
        expected_list: List[object] = expected
        actual_list: List[object] = actual
        assert len(actual_list) == len(
            expected_list
        ), f"At {path}: list length mismatch (expected {len(expected_list)}, got {len(actual_list)})"
        for i, (a, e) in enumerate(zip(actual_list, expected_list)):
            assert_structure_match(a, e, f"{path}[{i}]")
    else:
        # Direct comparison for other types
        assert actual == expected, f"At {path}: expected {expected}, got {actual}"
def test_search_non_existing_patterns(self) -> None:
    patterns = ["xyz", "apple", "cat"]
    for pattern in patterns:
        with self.subTest(pattern=pattern):
            assert not self.suffix_tree.search(pattern), (
                f"Pattern '{pattern}' should not be found."
            )

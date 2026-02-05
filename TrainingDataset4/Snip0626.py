def test_search_existing_patterns(self) -> None:
    patterns = ["ana", "ban", "na"]
    for pattern in patterns:
        with self.subTest(pattern=pattern):
            assert self.suffix_tree.search(pattern), (
                f"Pattern '{pattern}' should be found."
            )

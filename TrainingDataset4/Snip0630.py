def test_search_substrings(self) -> None:
    substrings = ["ban", "ana", "a", "na"]
    for substring in substrings:
        with self.subTest(substring=substring):
            assert self.suffix_tree.search(substring), (
                f"Substring '{substring}' should be found."
            )

def test_search_empty_pattern(self) -> None:
    assert self.suffix_tree.search(""), "An empty pattern should be found."

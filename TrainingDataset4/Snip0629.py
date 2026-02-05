def test_search_full_text(self) -> None:
    assert self.suffix_tree.search(self.text), (
        "The full text should be found in the suffix tree."
    )

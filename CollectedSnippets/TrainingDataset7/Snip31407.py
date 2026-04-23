def test_composed_index_with_fk(self):
        index = Index(fields=["author", "title"], name="book_author_title_idx")
        self._test_composed_index_with_fk(index)
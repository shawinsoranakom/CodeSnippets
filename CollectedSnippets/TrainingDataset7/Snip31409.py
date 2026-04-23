def test_composed_func_index_with_fk(self):
        index = Index(F("author"), F("title"), name="book_author_title_idx")
        self._test_composed_index_with_fk(index)
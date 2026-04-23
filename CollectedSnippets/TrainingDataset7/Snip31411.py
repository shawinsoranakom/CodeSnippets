def test_composed_func_transform_index_with_fk(self):
        index = Index(F("title__lower"), name="book_title_lower_idx")
        with register_lookup(CharField, Lower):
            self._test_composed_index_with_fk(index)
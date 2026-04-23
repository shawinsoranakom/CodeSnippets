def test_name_set(self):
        index_names = [index.name for index in Book._meta.indexes]
        self.assertCountEqual(
            index_names,
            [
                "model_index_title_196f42_idx",
                "model_index_isbn_34f975_idx",
                "model_indexes_book_barcode_idx",
            ],
        )
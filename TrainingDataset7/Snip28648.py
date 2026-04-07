def test_name_auto_generation(self):
        index = models.Index(fields=["author"])
        index.set_name_with_model(Book)
        self.assertEqual(index.name, "model_index_author_0f5565_idx")

        # '-' for DESC columns should be accounted for in the index name.
        index = models.Index(fields=["-author"])
        index.set_name_with_model(Book)
        self.assertEqual(index.name, "model_index_author_708765_idx")

        # fields may be truncated in the name. db_column is used for naming.
        long_field_index = models.Index(fields=["pages"])
        long_field_index.set_name_with_model(Book)
        self.assertEqual(long_field_index.name, "model_index_page_co_69235a_idx")

        # suffix can't be longer than 3 characters.
        long_field_index.suffix = "suff"
        msg = (
            "Index too long for multiple database support. Is self.suffix "
            "longer than 3 characters?"
        )
        with self.assertRaisesMessage(ValueError, msg):
            long_field_index.set_name_with_model(Book)
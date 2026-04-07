def test_index_fields_type(self):
        with self.assertRaisesMessage(
            ValueError, "Index.fields must be a list or tuple."
        ):
            models.Index(fields="title")
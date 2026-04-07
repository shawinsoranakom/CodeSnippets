def test_opclasses_requires_list_or_tuple(self):
        with self.assertRaisesMessage(
            ValueError, "Index.opclasses must be a list or tuple."
        ):
            models.Index(
                name="test_opclass", fields=["field"], opclasses="jsonb_path_ops"
            )
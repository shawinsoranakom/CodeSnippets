def test_custom_db_columns(self):
        model = CustomDbColumn.objects.create(custom_column=1)
        model.custom_column = 2
        CustomDbColumn.objects.bulk_update([model], fields=["custom_column"])
        model.refresh_from_db()
        self.assertEqual(model.custom_column, 2)
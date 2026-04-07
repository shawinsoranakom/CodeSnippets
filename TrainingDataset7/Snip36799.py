def test_unique_db_default(self):
        UniqueFieldsModel.objects.create(unique_charfield="foo", non_unique_field=42)
        um = UniqueFieldsModel(unique_charfield="bar", non_unique_field=42)
        with self.assertRaises(ValidationError) as cm:
            um.full_clean()
        self.assertEqual(
            cm.exception.message_dict,
            {
                "unique_integerfield": [
                    "Unique fields model with this Unique integerfield already exists."
                ]
            },
        )
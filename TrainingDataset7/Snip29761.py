def test_array_field(self):
        value = [
            {"a": 1, "b": "B", 2: "c", "ï": "ê"},
            {"a": 1, "b": "B", 2: "c", "ï": "ê"},
        ]
        expected_value = [
            {"a": "1", "b": "B", "2": "c", "ï": "ê"},
            {"a": "1", "b": "B", "2": "c", "ï": "ê"},
        ]
        instance = HStoreModel.objects.create(array_field=value)
        instance.refresh_from_db()
        self.assertEqual(instance.array_field, expected_value)
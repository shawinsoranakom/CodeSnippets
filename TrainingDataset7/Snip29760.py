def test_key_val_cast_to_string(self):
        value = {"a": 1, "b": "B", 2: "c", "ï": "ê"}
        expected_value = {"a": "1", "b": "B", "2": "c", "ï": "ê"}

        instance = HStoreModel.objects.create(field=value)
        instance = HStoreModel.objects.get()
        self.assertEqual(instance.field, expected_value)

        instance = HStoreModel.objects.get(field__a=1)
        self.assertEqual(instance.field, expected_value)

        instance = HStoreModel.objects.get(field__has_keys=[2, "a", "ï"])
        self.assertEqual(instance.field, expected_value)
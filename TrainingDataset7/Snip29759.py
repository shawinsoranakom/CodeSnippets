def test_value_null(self):
        value = {"a": None}
        instance = HStoreModel(field=value)
        instance.save()
        reloaded = HStoreModel.objects.get()
        self.assertEqual(reloaded.field, value)
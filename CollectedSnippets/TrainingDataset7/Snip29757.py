def test_save_load_success(self):
        value = {"a": "b"}
        instance = HStoreModel(field=value)
        instance.save()
        reloaded = HStoreModel.objects.get()
        self.assertEqual(reloaded.field, value)
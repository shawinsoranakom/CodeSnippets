def test_null(self):
        instance = HStoreModel(field=None)
        instance.save()
        reloaded = HStoreModel.objects.get()
        self.assertIsNone(reloaded.field)
def test_create_empty(self):
        NullDurationModel.objects.create()
        loaded = NullDurationModel.objects.get()
        self.assertIsNone(loaded.field)
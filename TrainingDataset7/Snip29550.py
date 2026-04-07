def test_char(self):
        instance = CharArrayModel(field=["hello", "goodbye"])
        instance.save()
        loaded = CharArrayModel.objects.get()
        self.assertEqual(instance.field, loaded.field)
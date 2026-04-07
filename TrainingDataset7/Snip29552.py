def test_tuples(self):
        instance = IntegerArrayModel(field=(1,))
        instance.save()
        loaded = IntegerArrayModel.objects.get()
        self.assertSequenceEqual(instance.field, loaded.field)
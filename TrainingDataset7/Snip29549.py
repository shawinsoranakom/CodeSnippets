def test_integer(self):
        instance = IntegerArrayModel(field=[1, 2, 3])
        instance.save()
        loaded = IntegerArrayModel.objects.get()
        self.assertEqual(instance.field, loaded.field)
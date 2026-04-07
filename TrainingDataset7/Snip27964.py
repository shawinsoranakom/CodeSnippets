def test_coercing(self):
        self.model.objects.create(value="10")
        instance = self.model.objects.get(value="10")
        self.assertEqual(instance.value, 10)
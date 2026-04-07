def test_default(self):
        obj = JSONNullDefaultModel.objects.create()
        self.assertIsNone(obj.value)
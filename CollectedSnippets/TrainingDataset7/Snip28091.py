def test_create(self):
        obj = JSONModel.objects.create(value=JSONNull())
        self.assertIsNone(obj.value)
def test_update(self):
        obj = JSONModel.objects.create(value={"key": "value"})
        JSONModel.objects.update(value=JSONNull())
        obj.refresh_from_db()
        self.assertIsNone(obj.value)
def test_save_load(self):
        obj = JSONModel(value=JSONNull())
        obj.save()
        self.assertIsNone(obj.value)
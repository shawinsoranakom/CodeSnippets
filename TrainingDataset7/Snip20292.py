def test_auto_field_subclass_create(self):
        obj = CustomAutoFieldModel.objects.create()
        self.assertIsInstance(obj.id, MyWrapper)
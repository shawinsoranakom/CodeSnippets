def test_auto_field_subclass_bulk_create(self):
        obj = CustomAutoFieldModel()
        CustomAutoFieldModel.objects.bulk_create([obj])
        self.assertIsInstance(obj.id, MyWrapper)
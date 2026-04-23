def test_model_set_on_base_field(self):
        instance = IntegerArrayModel()
        field = instance._meta.get_field("field")
        self.assertEqual(field.model, IntegerArrayModel)
        self.assertEqual(field.base_field.model, IntegerArrayModel)
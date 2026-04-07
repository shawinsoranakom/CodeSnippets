def test_model_and_reverse_model_should_equal_on_relations(self):
        for field in AllFieldsModel._meta.get_fields():
            is_concrete_forward_field = field.concrete and field.related_model
            if is_concrete_forward_field or field.many_to_many:
                reverse_field = field.remote_field
                self.assertEqual(field.model, reverse_field.related_model)
                self.assertEqual(field.related_model, reverse_field.model)
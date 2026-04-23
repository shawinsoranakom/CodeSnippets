def verify_max_length(self, model, field, length):
        self.assertEqual(model._meta.get_field(field).max_length, length)
def test_exist_single_field_output_field(self):
        queryset = Company.objects.values("pk")
        self.assertIsInstance(Exists(queryset).output_field, BooleanField)
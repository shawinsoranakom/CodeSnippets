def test_output_field_lookups(self):
        """Lookups from the output_field are available on GeneratedFields."""
        internal_type = IntegerField().get_internal_type()
        min_value, max_value = connection.ops.integer_field_range(internal_type)
        if min_value is None:
            self.skipTest("Backend doesn't define an integer min value.")
        if max_value is None:
            self.skipTest("Backend doesn't define an integer max value.")

        does_not_exist = self.base_model.DoesNotExist
        underflow_value = min_value - 1
        with self.assertNumQueries(0), self.assertRaises(does_not_exist):
            self.base_model.objects.get(field=underflow_value)
        with self.assertNumQueries(0), self.assertRaises(does_not_exist):
            self.base_model.objects.get(field__lt=underflow_value)
        with self.assertNumQueries(0), self.assertRaises(does_not_exist):
            self.base_model.objects.get(field__lte=underflow_value)

        overflow_value = max_value + 1
        with self.assertNumQueries(0), self.assertRaises(does_not_exist):
            self.base_model.objects.get(field=overflow_value)
        with self.assertNumQueries(0), self.assertRaises(does_not_exist):
            self.base_model.objects.get(field__gt=overflow_value)
        with self.assertNumQueries(0), self.assertRaises(does_not_exist):
            self.base_model.objects.get(field__gte=overflow_value)
def test_equal_output_field(self):
        value = Value("name", output_field=CharField())
        same_value = Value("name", output_field=CharField())
        other_value = Value("name", output_field=TimeField())
        no_output_field = Value("name")
        self.assertEqual(value, same_value)
        self.assertNotEqual(value, other_value)
        self.assertNotEqual(value, no_output_field)
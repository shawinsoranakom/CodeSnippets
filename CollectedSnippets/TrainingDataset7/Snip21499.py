def test_output_field_is_none_error(self):
        with self.assertRaises(OutputFieldIsNoneError):
            Employee.objects.annotate(custom_expression=Value(None)).first()
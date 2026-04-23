def test_already_converted_value(self):
        field = SimpleArrayField(forms.CharField())
        vals = ["a", "b", "c"]
        self.assertEqual(field.clean(vals), vals)
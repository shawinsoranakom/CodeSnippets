def test_prepare_value(self):
        field = SimpleArrayField(forms.CharField())
        value = field.prepare_value(["a", "b", "c"])
        self.assertEqual(value, "a,b,c")
def test_field_named_data(self):
        class DataForm(Form):
            data = CharField(max_length=10)

        f = DataForm({"data": "xyzzy"})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {"data": "xyzzy"})
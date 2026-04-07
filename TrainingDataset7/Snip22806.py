def test_custom_boundfield(self):
        class CustomField(CharField):
            def get_bound_field(self, form, name):
                return (form, name)

        class SampleForm(Form):
            name = CustomField()

        f = SampleForm()
        self.assertEqual(f["name"], (f, "name"))
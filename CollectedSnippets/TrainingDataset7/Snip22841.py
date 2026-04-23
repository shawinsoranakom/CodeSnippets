def test_custom_empty_values(self):
        """
        Form fields can customize what is considered as an empty value
        for themselves (#19997).
        """

        class CustomJSONField(CharField):
            empty_values = [None, ""]

            def to_python(self, value):
                # Fake json.loads
                if value == "{}":
                    return {}
                return super().to_python(value)

        class JSONForm(Form):
            json = CustomJSONField()

        form = JSONForm(data={"json": "{}"})
        form.full_clean()
        self.assertEqual(form.cleaned_data, {"json": {}})
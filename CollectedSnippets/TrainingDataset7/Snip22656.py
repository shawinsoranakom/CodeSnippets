def test_form_cleaned_data(self):
        form = ComplexFieldForm(
            {
                "field1_0": "some text",
                "field1_1": ["J", "P"],
                "field1_2_0": "2007-04-25",
                "field1_2_1": "06:24:00",
            }
        )
        form.is_valid()
        self.assertEqual(
            form.cleaned_data["field1"], "some text,JP,2007-04-25 06:24:00"
        )
def test_clean_disabled_multivalue(self):
        class ComplexFieldForm(Form):
            f = ComplexField(disabled=True, widget=ComplexMultiWidget)

        inputs = (
            "some text,JP,2007-04-25 06:24:00",
            ["some text", ["J", "P"], ["2007-04-25", "6:24:00"]],
        )
        for data in inputs:
            with self.subTest(data=data):
                form = ComplexFieldForm({}, initial={"f": data})
                form.full_clean()
                self.assertEqual(form.errors, {})
                self.assertEqual(form.cleaned_data, {"f": inputs[0]})
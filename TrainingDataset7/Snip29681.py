def test_splitarrayfield_remove_trailing_nulls_has_changed(self):
        class Form(forms.ModelForm):
            field = SplitArrayField(
                forms.IntegerField(), required=False, size=2, remove_trailing_nulls=True
            )

            class Meta:
                model = IntegerArrayModel
                fields = ("field",)

        tests = [
            ({}, {"field_0": "", "field_1": ""}, False),
            ({"field": None}, {"field_0": "", "field_1": ""}, False),
            ({"field": []}, {"field_0": "", "field_1": ""}, False),
            ({"field": [1]}, {"field_0": "1", "field_1": ""}, False),
        ]
        for initial, data, expected_result in tests:
            with self.subTest(initial=initial, data=data):
                obj = IntegerArrayModel(**initial)
                form = Form(data, instance=obj)
                self.assertIs(form.has_changed(), expected_result)
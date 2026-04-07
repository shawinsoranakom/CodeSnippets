def test_splitarrayfield_has_changed(self):
        class Form(forms.ModelForm):
            field = SplitArrayField(forms.IntegerField(), required=False, size=2)

            class Meta:
                model = IntegerArrayModel
                fields = ("field",)

        tests = [
            ({}, {"field_0": "", "field_1": ""}, True),
            ({"field": None}, {"field_0": "", "field_1": ""}, True),
            ({"field": [1]}, {"field_0": "", "field_1": ""}, True),
            ({"field": [1]}, {"field_0": "1", "field_1": "0"}, True),
            ({"field": [1, 2]}, {"field_0": "1", "field_1": "2"}, False),
            ({"field": [1, 2]}, {"field_0": "a", "field_1": "b"}, True),
        ]
        for initial, data, expected_result in tests:
            with self.subTest(initial=initial, data=data):
                obj = IntegerArrayModel(**initial)
                form = Form(data, instance=obj)
                self.assertIs(form.has_changed(), expected_result)
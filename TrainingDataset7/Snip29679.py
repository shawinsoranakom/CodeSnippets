def test_splitarraywidget_value_omitted_from_data(self):
        class Form(forms.ModelForm):
            field = SplitArrayField(forms.IntegerField(), required=False, size=2)

            class Meta:
                model = IntegerArrayModel
                fields = ("field",)

        form = Form({"field_0": "1", "field_1": "2"})
        self.assertEqual(form.errors, {})
        obj = form.save(commit=False)
        self.assertEqual(obj.field, [1, 2])
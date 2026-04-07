def test_queryset_none(self):
        class ModelChoiceForm(forms.Form):
            category = forms.ModelChoiceField(queryset=None)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["category"].queryset = Category.objects.filter(
                    slug__contains="test"
                )

        form = ModelChoiceForm()
        self.assertCountEqual(form.fields["category"].queryset, [self.c2, self.c3])
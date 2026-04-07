def test_result_cache_not_shared(self):
        class ModelChoiceForm(forms.Form):
            category = forms.ModelChoiceField(Category.objects.all())

        form1 = ModelChoiceForm()
        self.assertCountEqual(
            form1.fields["category"].queryset, [self.c1, self.c2, self.c3]
        )
        form2 = ModelChoiceForm()
        self.assertIsNone(form2.fields["category"].queryset._result_cache)
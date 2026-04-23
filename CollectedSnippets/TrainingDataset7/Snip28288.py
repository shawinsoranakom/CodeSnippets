def test_choices_bool_empty_label(self):
        f = forms.ModelChoiceField(Category.objects.all(), empty_label="--------")
        Category.objects.all().delete()
        self.assertIs(bool(f.choices), True)
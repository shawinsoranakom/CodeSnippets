def test_choices_bool(self):
        f = forms.ModelChoiceField(Category.objects.all(), empty_label=None)
        self.assertIs(bool(f.choices), True)
        Category.objects.all().delete()
        self.assertIs(bool(f.choices), False)
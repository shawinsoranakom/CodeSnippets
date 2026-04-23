def test_clean_to_field_name(self):
        f = forms.ModelChoiceField(Category.objects.all(), to_field_name="slug")
        self.assertEqual(f.clean(self.c1.slug), self.c1)
        self.assertEqual(f.clean(self.c1), self.c1)
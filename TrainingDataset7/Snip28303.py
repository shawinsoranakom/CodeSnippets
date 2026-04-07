def test_choices_not_fetched_when_not_rendering(self):
        with self.assertNumQueries(1):
            field = forms.ModelChoiceField(Category.objects.order_by("-name"))
            self.assertEqual("Entertainment", field.clean(self.c1.pk).name)
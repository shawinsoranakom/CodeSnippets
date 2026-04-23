def test_model_multiple_choice_number_of_queries(self):
        """
        ModelMultipleChoiceField does O(1) queries instead of O(n) (#10156).
        """
        persons = [Writer.objects.create(name="Person %s" % i) for i in range(30)]

        f = forms.ModelMultipleChoiceField(queryset=Writer.objects.all())
        self.assertNumQueries(1, f.clean, [p.pk for p in persons[1:11:2]])
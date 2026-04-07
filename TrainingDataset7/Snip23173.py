def test_empty_queryset_return(self):
        """
        If a model's ManyToManyField has blank=True and is saved with no data,
        a queryset is returned.
        """
        option = ChoiceOptionModel.objects.create(name="default")
        form = OptionalMultiChoiceModelForm(
            {"multi_choice_optional": "", "multi_choice": [option.pk]}
        )
        self.assertTrue(form.is_valid())
        # The empty value is a QuerySet
        self.assertIsInstance(
            form.cleaned_data["multi_choice_optional"], models.query.QuerySet
        )
        # While we're at it, test whether a QuerySet is returned if there *is*
        # a value.
        self.assertIsInstance(form.cleaned_data["multi_choice"], models.query.QuerySet)
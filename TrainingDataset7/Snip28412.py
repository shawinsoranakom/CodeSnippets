def test_model_multiple_choice_show_hidden_initial(self):
        """
        Test support of show_hidden_initial by ModelMultipleChoiceField.
        """

        class WriterForm(forms.Form):
            persons = forms.ModelMultipleChoiceField(
                show_hidden_initial=True, queryset=Writer.objects.all()
            )

        person1 = Writer.objects.create(name="Person 1")
        person2 = Writer.objects.create(name="Person 2")

        form = WriterForm(
            initial={"persons": [person1, person2]},
            data={
                "initial-persons": [str(person1.pk), str(person2.pk)],
                "persons": [str(person1.pk), str(person2.pk)],
            },
        )
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_changed())

        form = WriterForm(
            initial={"persons": [person1, person2]},
            data={
                "initial-persons": [str(person1.pk), str(person2.pk)],
                "persons": [str(person2.pk)],
            },
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.has_changed())
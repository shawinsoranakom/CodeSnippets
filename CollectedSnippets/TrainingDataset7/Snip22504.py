def test_choicefield_callable_may_evaluate_to_different_values(self):
        choices = []

        def choices_as_callable():
            return choices

        class ChoiceFieldForm(Form):
            choicefield = ChoiceField(choices=choices_as_callable)

        choices = [("J", "John")]
        form = ChoiceFieldForm()
        self.assertEqual(choices, list(form.fields["choicefield"].choices))
        self.assertEqual(choices, list(form.fields["choicefield"].widget.choices))

        choices = [("P", "Paul")]
        form = ChoiceFieldForm()
        self.assertEqual(choices, list(form.fields["choicefield"].choices))
        self.assertEqual(choices, list(form.fields["choicefield"].widget.choices))
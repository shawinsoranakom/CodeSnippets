def test_no_empty_option(self):
        """
        If a model's ForeignKey has blank=False and a default, no empty option
        is created.
        """
        option = ChoiceOptionModel.objects.create(name="default")

        choices = list(ChoiceFieldForm().fields["choice"].choices)
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0], (option.pk, str(option)))
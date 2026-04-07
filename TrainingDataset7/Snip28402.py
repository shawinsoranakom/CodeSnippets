def test_callable_choices_are_lazy(self):
        call_count = 0

        def get_animal_choices():
            nonlocal call_count
            call_count += 1
            return [("LION", "Lion"), ("ZEBRA", "Zebra")]

        class ZooKeeper(models.Model):
            animal = models.CharField(
                blank=True,
                choices=get_animal_choices,
                max_length=5,
            )

        class ZooKeeperForm(forms.ModelForm):
            class Meta:
                model = ZooKeeper
                fields = ["animal"]

        self.assertEqual(call_count, 0)
        form = ZooKeeperForm()
        self.assertEqual(call_count, 0)
        self.assertIsInstance(form.fields["animal"].choices, BlankChoiceIterator)
        self.assertEqual(call_count, 0)
        self.assertEqual(
            form.fields["animal"].choices,
            models.BLANK_CHOICE_DASH + [("LION", "Lion"), ("ZEBRA", "Zebra")],
        )
        self.assertEqual(call_count, 1)
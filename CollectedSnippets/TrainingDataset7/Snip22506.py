def test_choicefield_enumeration(self):
        class FirstNames(models.TextChoices):
            JOHN = "J", "John"
            PAUL = "P", "Paul"

        f = ChoiceField(choices=FirstNames)
        self.assertEqual(f.choices, FirstNames.choices)
        self.assertEqual(f.clean("J"), "J")
        msg = "'Select a valid choice. 3 is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("3")
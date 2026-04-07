def test_booleanfield_choices_blank_desired(self):
        """
        BooleanField with choices and no default should generated a formfield
        with the blank option.
        """
        choices = [(1, "Si"), (2, "No")]
        f = models.BooleanField(choices=choices)
        self.assertEqual(f.formfield().choices, [("", "---------")] + choices)
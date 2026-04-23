def test_booleanfield_choices_blank(self):
        """
        BooleanField with choices and defaults doesn't generate a formfield
        with the blank option (#9640, #10549).
        """
        choices = [(1, "Si"), (2, "No")]
        f = models.BooleanField(choices=choices, default=1, null=False)
        self.assertEqual(f.formfield().choices, choices)
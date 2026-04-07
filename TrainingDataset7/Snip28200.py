def test_choices_form_class(self):
        """Can supply a custom choices form class to Field.formfield()"""
        choices = [("a", "a")]
        field = models.CharField(choices=choices)
        klass = forms.TypedMultipleChoiceField
        self.assertIsInstance(field.formfield(choices_form_class=klass), klass)
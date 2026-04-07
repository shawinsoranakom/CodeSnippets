def test_formfield_disabled(self):
        """Field.formfield() sets disabled for fields with choices."""
        field = models.CharField(choices=[("a", "b")])
        form_field = field.formfield(disabled=True)
        self.assertIs(form_field.disabled, True)
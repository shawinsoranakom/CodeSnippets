def test_recleaning_model_form_instance(self):
        """
        Re-cleaning an instance that was added via a ModelForm shouldn't raise
        a pk uniqueness error.
        """

        class AuthorForm(forms.ModelForm):
            class Meta:
                model = Author
                fields = "__all__"

        form = AuthorForm({"full_name": "Bob"})
        self.assertTrue(form.is_valid())
        obj = form.save()
        obj.name = "Alice"
        obj.full_clean()
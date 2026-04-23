def test_override_clean(self):
        """
        Regression for #12596: Calling super from ModelForm.clean() should be
        optional.
        """

        class TripleFormWithCleanOverride(forms.ModelForm):
            class Meta:
                model = Triple
                fields = "__all__"

            def clean(self):
                if not self.cleaned_data["left"] == self.cleaned_data["right"]:
                    raise ValidationError("Left and right should be equal")
                return self.cleaned_data

        form = TripleFormWithCleanOverride({"left": 1, "middle": 2, "right": 1})
        self.assertTrue(form.is_valid())
        # form.instance.left will be None if the instance was not constructed
        # by form.full_clean().
        self.assertEqual(form.instance.left, 1)
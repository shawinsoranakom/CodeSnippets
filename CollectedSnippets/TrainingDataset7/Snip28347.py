def test_invalid_meta_model(self):
        class InvalidModelForm(forms.ModelForm):
            class Meta:
                pass  # no model

        # Can't create new form
        msg = "ModelForm has no model class specified."
        with self.assertRaisesMessage(ValueError, msg):
            InvalidModelForm()

        # Even if you provide a model instance
        with self.assertRaisesMessage(ValueError, msg):
            InvalidModelForm(instance=Category)
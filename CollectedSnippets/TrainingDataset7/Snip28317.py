def test_no_model_class(self):
        class NoModelModelForm(forms.ModelForm):
            pass

        with self.assertRaisesMessage(
            ValueError, "ModelForm has no model class specified."
        ):
            NoModelModelForm()
def test_custom_file_field_save(self):
        """
        Regression for #11149: save_form_data should be called only once
        """

        class CFFForm(forms.ModelForm):
            class Meta:
                model = CustomFF
                fields = "__all__"

        # It's enough that the form saves without error -- the custom save
        # routine will generate an AssertionError if it is called more than
        # once during save.
        form = CFFForm(data={"f": None})
        form.save()
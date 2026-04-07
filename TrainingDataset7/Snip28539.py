def test_inline_formsets_with_custom_save_method_related_instance(self):
        """
        The ModelForm.save() method should be able to access the related object
        if it exists in the database (#24395).
        """

        class PoemForm2(forms.ModelForm):
            def save(self, commit=True):
                poem = super().save(commit=False)
                poem.name = "%s by %s" % (poem.name, poem.poet.name)
                if commit:
                    poem.save()
                return poem

        PoemFormSet = inlineformset_factory(
            Poet, Poem, form=PoemForm2, fields="__all__"
        )
        data = {
            "poem_set-TOTAL_FORMS": "1",
            "poem_set-INITIAL_FORMS": "0",
            "poem_set-MAX_NUM_FORMS": "",
            "poem_set-0-name": "Le Lac",
        }
        poet = Poet()
        formset = PoemFormSet(data=data, instance=poet)
        self.assertTrue(formset.is_valid())

        # The Poet instance is saved after the formset instantiation. This
        # happens in admin's changeform_view() when adding a new object and
        # some inlines in the same request.
        poet.name = "Lamartine"
        poet.save()
        poem = formset.save()[0]
        self.assertEqual(poem.name, "Le Lac by Lamartine")
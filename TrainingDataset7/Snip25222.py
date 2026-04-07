def test_fk_in_all_formset_forms(self):
        """
        A foreign key field is in Meta for all forms in the formset (#26538).
        """

        class PoemModelForm(ModelForm):
            def __init__(self, *args, **kwargs):
                assert "poet" in self._meta.fields
                super().__init__(*args, **kwargs)

        poet = Poet.objects.create(name="test")
        poet.poem_set.create(name="first test poem")
        poet.poem_set.create(name="second test poem")
        PoemFormSet = inlineformset_factory(
            Poet, Poem, form=PoemModelForm, fields=("name",), extra=0
        )
        formset = PoemFormSet(None, instance=poet)
        formset.forms
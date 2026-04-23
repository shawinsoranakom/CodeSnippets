def test_fk_not_duplicated_in_form_fields(self):
        """
        A foreign key name isn't duplicated in form._meta fields (#21332).
        """
        poet = Poet.objects.create(name="test")
        poet.poem_set.create(name="first test poem")
        poet.poem_set.create(name="second test poem")
        poet.poem_set.create(name="third test poem")
        PoemFormSet = inlineformset_factory(Poet, Poem, fields=("name",), extra=0)
        formset = PoemFormSet(None, instance=poet)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(["name", "poet"], PoemFormSet.form._meta.fields)
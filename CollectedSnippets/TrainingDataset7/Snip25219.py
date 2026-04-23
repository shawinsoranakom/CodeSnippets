def test_zero_primary_key(self):
        # Regression test for #21472
        poet = Poet.objects.create(id=0, name="test")
        poet.poem_set.create(name="test poem")
        PoemFormSet = inlineformset_factory(Poet, Poem, fields="__all__", extra=0)
        formset = PoemFormSet(None, instance=poet)
        self.assertEqual(len(formset.forms), 1)
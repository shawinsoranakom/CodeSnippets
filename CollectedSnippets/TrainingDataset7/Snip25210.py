def test_deletion(self):
        PoemFormSet = inlineformset_factory(
            Poet, Poem, can_delete=True, fields="__all__"
        )
        poet = Poet.objects.create(name="test")
        poem = poet.poem_set.create(name="test poem")
        data = {
            "poem_set-TOTAL_FORMS": "1",
            "poem_set-INITIAL_FORMS": "1",
            "poem_set-MAX_NUM_FORMS": "0",
            "poem_set-0-id": str(poem.pk),
            "poem_set-0-poet": str(poet.pk),
            "poem_set-0-name": "test",
            "poem_set-0-DELETE": "on",
        }
        formset = PoemFormSet(data, instance=poet)
        formset.save()
        self.assertTrue(formset.is_valid())
        self.assertEqual(Poem.objects.count(), 0)
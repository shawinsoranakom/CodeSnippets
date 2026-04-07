def test_outdated_deletion(self):
        poet = Poet.objects.create(name="test")
        poem = Poem.objects.create(name="Brevity is the soul of wit", poet=poet)

        PoemFormSet = inlineformset_factory(
            Poet, Poem, fields="__all__", can_delete=True
        )

        # Simulate deletion of an object that doesn't exist in the database
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-0-id": str(poem.pk),
            "form-0-name": "foo",
            "form-1-id": str(poem.pk + 1),  # doesn't exist
            "form-1-name": "bar",
            "form-1-DELETE": "on",
        }
        formset = PoemFormSet(data, instance=poet, prefix="form")

        # The formset is valid even though poem.pk + 1 doesn't exist,
        # because it's marked for deletion anyway
        self.assertTrue(formset.is_valid())

        formset.save()

        # Make sure the save went through correctly
        self.assertEqual(Poem.objects.get(pk=poem.pk).name, "foo")
        self.assertEqual(poet.poem_set.count(), 1)
        self.assertFalse(Poem.objects.filter(pk=poem.pk + 1).exists())
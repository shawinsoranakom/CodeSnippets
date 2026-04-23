def test_change_form_deletion_when_invalid(self):
        """
        Make sure that a change form that is filled out, but marked for
        deletion doesn't cause validation errors.
        """
        PoemFormSet = inlineformset_factory(
            Poet, Poem, can_delete=True, fields="__all__"
        )
        poet = Poet.objects.create(name="test")
        poem = poet.poem_set.create(name="test poem")
        data = {
            "poem_set-TOTAL_FORMS": "1",
            "poem_set-INITIAL_FORMS": "1",
            "poem_set-MAX_NUM_FORMS": "0",
            "poem_set-0-id": str(poem.id),
            "poem_set-0-poem": str(poem.id),
            "poem_set-0-name": "x" * 1000,
        }
        formset = PoemFormSet(data, instance=poet)
        # Make sure this form doesn't pass validation.
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(Poem.objects.count(), 1)

        # Then make sure that it *does* pass validation and delete the object,
        # even though the data isn't actually valid.
        data["poem_set-0-DELETE"] = "on"
        formset = PoemFormSet(data, instance=poet)
        self.assertIs(formset.is_valid(), True)
        formset.save()
        self.assertEqual(Poem.objects.count(), 0)
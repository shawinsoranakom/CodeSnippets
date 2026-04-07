def test_change_form_deletion_when_invalid(self):
        """
        Make sure that a change form that is filled out, but marked for
        deletion doesn't cause validation errors.
        """
        PoetFormSet = modelformset_factory(Poet, fields="__all__", can_delete=True)
        poet = Poet.objects.create(name="test")
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(poet.id),
            "form-0-name": "x" * 1000,
        }
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        # Make sure this form doesn't pass validation.
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(Poet.objects.count(), 1)

        # Then make sure that it *does* pass validation and delete the object,
        # even though the data isn't actually valid.
        data["form-0-DELETE"] = "on"
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        self.assertIs(formset.is_valid(), True)
        formset.save()
        self.assertEqual(Poet.objects.count(), 0)
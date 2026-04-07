def test_add_form_deletion_when_invalid(self):
        """
        Make sure that an add form that is filled out, but marked for deletion
        doesn't cause validation errors.
        """
        PoetFormSet = modelformset_factory(Poet, fields="__all__", can_delete=True)
        poet = Poet.objects.create(name="test")
        # One existing untouched and two new unvalid forms
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(poet.id),
            "form-0-name": "test",
            "form-1-id": "",
            "form-1-name": "x" * 1000,  # Too long
            "form-2-id": str(poet.id),  # Violate unique constraint
            "form-2-name": "test2",
        }
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        # Make sure this form doesn't pass validation.
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(Poet.objects.count(), 1)

        # Then make sure that it *does* pass validation and delete the object,
        # even though the data in new forms aren't actually valid.
        data["form-0-DELETE"] = "on"
        data["form-1-DELETE"] = "on"
        data["form-2-DELETE"] = "on"
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        self.assertIs(formset.is_valid(), True)
        formset.save()
        self.assertEqual(Poet.objects.count(), 0)
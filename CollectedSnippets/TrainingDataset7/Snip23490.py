def test_save_as_new(self):
        """
        The save_as_new parameter creates new items that are associated with
        the object.
        """
        lion = Animal.objects.create(common_name="Lion", latin_name="Panthera leo")
        yellow = lion.tags.create(tag="yellow")
        hairy = lion.tags.create(tag="hairy")
        GenericFormSet = generic_inlineformset_factory(TaggedItem)
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "2",
            "form-MAX_NUM_FORMS": "",
            "form-0-id": str(yellow.pk),
            "form-0-tag": "hunts",
            "form-1-id": str(hairy.pk),
            "form-1-tag": "roars",
        }
        formset = GenericFormSet(data, instance=lion, prefix="form", save_as_new=True)
        self.assertTrue(formset.is_valid())
        tags = formset.save()
        self.assertEqual([tag.tag for tag in tags], ["hunts", "roars"])
        hunts, roars = tags
        self.assertSequenceEqual(
            lion.tags.order_by("tag"), [hairy, hunts, roars, yellow]
        )
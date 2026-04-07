def test_filtered_default_manager(self):
        """Even though the default manager filters out some records,
        we must still be able to save (particularly, save by updating
        existing records) those filtered instances. This is a
        regression test for #8990, #9527"""
        related = RelatedModel.objects.create(name="xyzzy")
        obj = RestrictedModel.objects.create(name="hidden", related=related)
        obj.name = "still hidden"
        obj.save()

        # If the hidden object wasn't seen during the save process,
        # there would now be two objects in the database.
        self.assertEqual(RestrictedModel.plain_manager.count(), 1)
def test_delete_related_on_filtered_manager(self):
        """Deleting related objects should also not be distracted by a
        restricted manager on the related object. This is a regression
        test for #2698."""
        related = RelatedModel.objects.create(name="xyzzy")

        for name, public in (("one", True), ("two", False), ("three", False)):
            RestrictedModel.objects.create(name=name, is_public=public, related=related)

        obj = RelatedModel.objects.get(name="xyzzy")
        obj.delete()

        # All of the RestrictedModel instances should have been
        # deleted, since they *all* pointed to the RelatedModel. If
        # the default manager is used, only the public one will be
        # deleted.
        self.assertEqual(len(RestrictedModel.plain_manager.all()), 0)
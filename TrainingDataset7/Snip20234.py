def test_delete_one_to_one_manager(self):
        # The same test case as the last one, but for one-to-one
        # models, which are implemented slightly different internally,
        # so it's a different code path.
        obj = RelatedModel.objects.create(name="xyzzy")
        OneToOneRestrictedModel.objects.create(name="foo", is_public=False, related=obj)
        obj = RelatedModel.objects.get(name="xyzzy")
        obj.delete()
        self.assertEqual(len(OneToOneRestrictedModel.plain_manager.all()), 0)
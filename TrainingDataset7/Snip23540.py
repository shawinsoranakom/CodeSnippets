def test_update_or_create_defaults(self):
        # update_or_create should work with virtual fields (content_object)
        quartz = Mineral.objects.create(name="Quartz", hardness=7)
        diamond = Mineral.objects.create(name="Diamond", hardness=7)
        tag, created = TaggedItem.objects.update_or_create(
            tag="shiny", defaults={"content_object": quartz}
        )
        self.assertTrue(created)
        self.assertEqual(tag.content_object.id, quartz.id)

        tag, created = TaggedItem.objects.update_or_create(
            tag="shiny", defaults={"content_object": diamond}
        )
        self.assertFalse(created)
        self.assertEqual(tag.content_object.id, diamond.id)
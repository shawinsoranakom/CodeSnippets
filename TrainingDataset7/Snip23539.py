def test_get_or_create(self):
        # get_or_create should work with virtual fields (content_object)
        quartz = Mineral.objects.create(name="Quartz", hardness=7)
        tag, created = TaggedItem.objects.get_or_create(
            tag="shiny", defaults={"content_object": quartz}
        )
        self.assertTrue(created)
        self.assertEqual(tag.tag, "shiny")
        self.assertEqual(tag.content_object.id, quartz.id)
def test_update_or_create_defaults_with_create_defaults(self):
        # update_or_create() should work with virtual fields (content_object).
        quartz = Mineral.objects.create(name="Quartz", hardness=7)
        diamond = Mineral.objects.create(name="Diamond", hardness=7)
        tag, created = TaggedItem.objects.update_or_create(
            tag="shiny",
            create_defaults={"content_object": quartz},
            defaults={"content_object": diamond},
        )
        self.assertIs(created, True)
        self.assertEqual(tag.content_object.id, quartz.id)

        tag, created = TaggedItem.objects.update_or_create(
            tag="shiny",
            create_defaults={"content_object": quartz},
            defaults={"content_object": diamond},
        )
        self.assertIs(created, False)
        self.assertEqual(tag.content_object.id, diamond.id)
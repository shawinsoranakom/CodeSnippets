def test_gfk_manager(self):
        # GenericForeignKey should not use the default manager (which may
        # filter objects).
        tailless = Gecko.objects.create(has_tail=False)
        tag = TaggedItem.objects.create(content_object=tailless, tag="lizard")
        self.assertEqual(tag.content_object, tailless)
def test_set_after_prefetch(self):
        platypus = Animal.objects.prefetch_related("tags").get(pk=self.platypus.pk)
        self.assertSequenceEqual(platypus.tags.all(), [])
        furry_tag = TaggedItem.objects.create(tag="furry", content_object=platypus)
        platypus.tags.set([furry_tag])
        self.assertSequenceEqual(platypus.tags.all(), [furry_tag])
        weird_tag = TaggedItem.objects.create(tag="weird", content_object=platypus)
        platypus.tags.set([weird_tag])
        self.assertSequenceEqual(platypus.tags.all(), [weird_tag])
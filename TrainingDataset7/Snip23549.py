def test_add_after_prefetch(self):
        platypus = Animal.objects.prefetch_related("tags").get(pk=self.platypus.pk)
        self.assertSequenceEqual(platypus.tags.all(), [])
        weird_tag = TaggedItem.objects.create(tag="weird", content_object=platypus)
        platypus.tags.add(weird_tag)
        self.assertSequenceEqual(platypus.tags.all(), [weird_tag])
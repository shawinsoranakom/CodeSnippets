def test_add_then_remove_after_prefetch(self):
        furry_tag = self.platypus.tags.create(tag="furry")
        platypus = Animal.objects.prefetch_related("tags").get(pk=self.platypus.pk)
        self.assertSequenceEqual(platypus.tags.all(), [furry_tag])
        weird_tag = self.platypus.tags.create(tag="weird")
        platypus.tags.add(weird_tag)
        self.assertSequenceEqual(platypus.tags.all(), [furry_tag, weird_tag])
        platypus.tags.remove(weird_tag)
        self.assertSequenceEqual(platypus.tags.all(), [furry_tag])
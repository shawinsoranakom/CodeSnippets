def test_remove_after_prefetch(self):
        weird_tag = self.platypus.tags.create(tag="weird")
        platypus = Animal.objects.prefetch_related("tags").get(pk=self.platypus.pk)
        self.assertSequenceEqual(platypus.tags.all(), [weird_tag])
        platypus.tags.remove(weird_tag)
        self.assertSequenceEqual(platypus.tags.all(), [])
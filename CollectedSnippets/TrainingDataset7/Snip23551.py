def test_clear_after_prefetch(self):
        weird_tag = self.platypus.tags.create(tag="weird")
        platypus = Animal.objects.prefetch_related("tags").get(pk=self.platypus.pk)
        self.assertSequenceEqual(platypus.tags.all(), [weird_tag])
        platypus.tags.clear()
        self.assertSequenceEqual(platypus.tags.all(), [])
def test_create_after_prefetch(self):
        platypus = Animal.objects.prefetch_related("tags").get(pk=self.platypus.pk)
        self.assertSequenceEqual(platypus.tags.all(), [])
        weird_tag = platypus.tags.create(tag="weird")
        self.assertSequenceEqual(platypus.tags.all(), [weird_tag])
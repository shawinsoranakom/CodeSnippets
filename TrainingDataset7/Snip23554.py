def test_prefetch_related_different_content_types(self):
        TaggedItem.objects.create(content_object=self.platypus, tag="prefetch_tag_1")
        TaggedItem.objects.create(
            content_object=Vegetable.objects.create(name="Broccoli"),
            tag="prefetch_tag_2",
        )
        TaggedItem.objects.create(
            content_object=Animal.objects.create(common_name="Bear"),
            tag="prefetch_tag_3",
        )
        qs = TaggedItem.objects.filter(
            tag__startswith="prefetch_tag_",
        ).prefetch_related("content_object", "content_object__tags")
        with self.assertNumQueries(4):
            tags = list(qs)
        for tag in tags:
            self.assertSequenceEqual(tag.content_object.tags.all(), [tag])
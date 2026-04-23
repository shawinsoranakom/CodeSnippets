def test_cache_invalidation_for_object_id(self):
        broccoli = Vegetable.objects.create(name="Broccoli")
        cauliflower = Vegetable.objects.create(name="Cauliflower")
        tag = TaggedItem.objects.create(content_object=broccoli, tag="yummy")
        tag.object_id = cauliflower.id
        self.assertEqual(tag.content_object, cauliflower)
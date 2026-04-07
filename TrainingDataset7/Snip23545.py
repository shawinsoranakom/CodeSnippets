def test_cache_invalidation_for_content_type_id(self):
        # Create a Vegetable and Mineral with the same id.
        new_id = (
            max(
                Vegetable.objects.order_by("-id")[0].id,
                Mineral.objects.order_by("-id")[0].id,
            )
            + 1
        )
        broccoli = Vegetable.objects.create(id=new_id, name="Broccoli")
        diamond = Mineral.objects.create(id=new_id, name="Diamond", hardness=7)
        tag = TaggedItem.objects.create(content_object=broccoli, tag="yummy")
        tag.content_type = ContentType.objects.get_for_model(diamond)
        self.assertEqual(tag.content_object, diamond)
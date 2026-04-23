def test_prefetch_GFK_uses_prepped_primary_key(self):
        article = ArticleCustomUUID.objects.create(name="Blanche")
        Comment.objects.create(comment="Enchantment", content_object_uuid=article)
        obj = Comment.objects.prefetch_related("content_object_uuid").get(
            comment="Enchantment"
        )
        self.assertEqual(obj.content_object_uuid, article)
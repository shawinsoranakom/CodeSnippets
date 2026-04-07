def test_prefetch_GFK_uuid_pk(self):
        article = Article.objects.create(name="Django")
        Comment.objects.create(comment="awesome", content_object_uuid=article)
        qs = Comment.objects.prefetch_related("content_object_uuid")
        self.assertEqual([c.content_object_uuid for c in qs], [article])
def test_first_last_unordered_qs_aggregation_error(self):
        a1 = Article.objects.create(
            headline="Article 1",
            pub_date=datetime(2005, 7, 26),
            expire_date=datetime(2005, 9, 1),
        )
        Comment.objects.create(article=a1, likes_count=5)

        qs = Comment.objects.values("article").annotate(avg_likes=Avg("likes_count"))
        msg = (
            "Cannot use QuerySet.%s() on an unordered queryset performing aggregation. "
            "Add an ordering with order_by()."
        )
        with self.assertRaisesMessage(TypeError, msg % "first"):
            qs.first()
        with self.assertRaisesMessage(TypeError, msg % "last"):
            qs.last()
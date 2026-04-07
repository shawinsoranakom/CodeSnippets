def test_order_by_ptr_field_with_default_ordering_by_expression(self):
        ca1 = ChildArticle.objects.create(
            headline="h2",
            pub_date=datetime(2005, 7, 27),
            author=self.author_2,
        )
        ca2 = ChildArticle.objects.create(
            headline="h2",
            pub_date=datetime(2005, 7, 27),
            author=self.author_1,
        )
        ca3 = ChildArticle.objects.create(
            headline="h3",
            pub_date=datetime(2005, 7, 27),
            author=self.author_1,
        )
        ca4 = ChildArticle.objects.create(headline="h1", pub_date=datetime(2005, 7, 28))
        articles = ChildArticle.objects.order_by("article_ptr")
        self.assertSequenceEqual(articles, [ca4, ca2, ca1, ca3])
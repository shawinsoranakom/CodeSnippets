def test_orders_nulls_first_on_filtered_subquery(self):
        Article.objects.filter(headline="Article 1").update(author=self.author_1)
        Article.objects.filter(headline="Article 2").update(author=self.author_1)
        Article.objects.filter(headline="Article 4").update(author=self.author_2)
        Author.objects.filter(name__isnull=True).delete()
        author_3 = Author.objects.create(name="Name 3")
        article_subquery = (
            Article.objects.filter(
                author=OuterRef("pk"),
                headline__icontains="Article",
            )
            .order_by()
            .values("author")
            .annotate(
                last_date=Max("pub_date"),
            )
            .values("last_date")
        )
        self.assertQuerySetEqualReversible(
            Author.objects.annotate(
                last_date=Subquery(article_subquery, output_field=DateTimeField())
            )
            .order_by(F("last_date").asc(nulls_first=True))
            .distinct(),
            [author_3, self.author_1, self.author_2],
        )
def test_reverse_meta_ordering_pure(self):
        Article.objects.create(
            headline="Article 5",
            pub_date=datetime(2005, 7, 30),
            author=self.author_1,
            second_author=self.author_2,
        )
        Article.objects.create(
            headline="Article 5",
            pub_date=datetime(2005, 7, 30),
            author=self.author_2,
            second_author=self.author_1,
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline="Article 5").reverse(),
            ["Name 2", "Name 1"],
            attrgetter("author.name"),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(headline="Article 5"),
            ["Name 1", "Name 2"],
            attrgetter("author.name"),
        )
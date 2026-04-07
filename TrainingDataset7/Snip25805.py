def test_values_relations(self):
        # You can specify fields from forward and reverse relations, just like
        # filter().
        self.assertSequenceEqual(
            Article.objects.values("headline", "author__name"),
            [
                {"headline": self.a5.headline, "author__name": self.au2.name},
                {"headline": self.a6.headline, "author__name": self.au2.name},
                {"headline": self.a4.headline, "author__name": self.au1.name},
                {"headline": self.a2.headline, "author__name": self.au1.name},
                {"headline": self.a3.headline, "author__name": self.au1.name},
                {"headline": self.a7.headline, "author__name": self.au2.name},
                {"headline": self.a1.headline, "author__name": self.au1.name},
            ],
        )
        self.assertSequenceEqual(
            Author.objects.values("name", "article__headline").order_by(
                "name", "article__headline"
            ),
            [
                {"name": self.au1.name, "article__headline": self.a1.headline},
                {"name": self.au1.name, "article__headline": self.a2.headline},
                {"name": self.au1.name, "article__headline": self.a3.headline},
                {"name": self.au1.name, "article__headline": self.a4.headline},
                {"name": self.au2.name, "article__headline": self.a5.headline},
                {"name": self.au2.name, "article__headline": self.a6.headline},
                {"name": self.au2.name, "article__headline": self.a7.headline},
            ],
        )
        self.assertSequenceEqual(
            (
                Author.objects.values(
                    "name", "article__headline", "article__tag__name"
                ).order_by("name", "article__headline", "article__tag__name")
            ),
            [
                {
                    "name": self.au1.name,
                    "article__headline": self.a1.headline,
                    "article__tag__name": self.t1.name,
                },
                {
                    "name": self.au1.name,
                    "article__headline": self.a2.headline,
                    "article__tag__name": self.t1.name,
                },
                {
                    "name": self.au1.name,
                    "article__headline": self.a3.headline,
                    "article__tag__name": self.t1.name,
                },
                {
                    "name": self.au1.name,
                    "article__headline": self.a3.headline,
                    "article__tag__name": self.t2.name,
                },
                {
                    "name": self.au1.name,
                    "article__headline": self.a4.headline,
                    "article__tag__name": self.t2.name,
                },
                {
                    "name": self.au2.name,
                    "article__headline": self.a5.headline,
                    "article__tag__name": self.t2.name,
                },
                {
                    "name": self.au2.name,
                    "article__headline": self.a5.headline,
                    "article__tag__name": self.t3.name,
                },
                {
                    "name": self.au2.name,
                    "article__headline": self.a6.headline,
                    "article__tag__name": self.t3.name,
                },
                {
                    "name": self.au2.name,
                    "article__headline": self.a7.headline,
                    "article__tag__name": self.t3.name,
                },
            ],
        )
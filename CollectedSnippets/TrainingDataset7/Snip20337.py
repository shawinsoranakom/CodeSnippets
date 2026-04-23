def test_mixed_values(self):
        a1 = Author.objects.create(name="John Smith", alias="smithj")
        a2 = Author.objects.create(name="Rhonda")
        ar1 = Article.objects.create(
            title="How to Django",
            text=lorem_ipsum,
            written=timezone.now(),
        )
        ar1.authors.add(a1)
        ar1.authors.add(a2)
        # mixed Text and Char
        article = Article.objects.annotate(
            headline=Coalesce("summary", "text", output_field=TextField()),
        )
        self.assertQuerySetEqual(
            article.order_by("title"), [lorem_ipsum], lambda a: a.headline
        )
        # mixed Text and Char wrapped
        article = Article.objects.annotate(
            headline=Coalesce(
                Lower("summary"), Lower("text"), output_field=TextField()
            ),
        )
        self.assertQuerySetEqual(
            article.order_by("title"), [lorem_ipsum.lower()], lambda a: a.headline
        )
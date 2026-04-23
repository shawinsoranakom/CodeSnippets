def test_hash_function(self):
        # Model instances have a hash function, so they can be used in sets
        # or as dictionary keys. Two models compare as equal if their primary
        # keys are equal.
        a10 = Article.objects.create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a11 = Article.objects.create(
            headline="Article 11",
            pub_date=datetime(2008, 1, 1),
        )
        a12 = Article.objects.create(
            headline="Article 12",
            pub_date=datetime(2008, 12, 31, 23, 59, 59, 999999),
        )

        s = {a10, a11, a12}
        self.assertIn(Article.objects.get(headline="Article 11"), s)
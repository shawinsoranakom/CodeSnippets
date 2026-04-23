def test_querysets_checking_for_membership(self):
        headlines = ["Parrot programs in Python", "Second article", "Third article"]
        some_pub_date = datetime(2014, 5, 16, 12, 1)
        for headline in headlines:
            Article(headline=headline, pub_date=some_pub_date).save()
        a = Article(headline="Some headline", pub_date=some_pub_date)
        a.save()

        # You can use 'in' to test for membership...
        self.assertIn(a, Article.objects.all())
        # ... but there will often be more efficient ways if that is all you
        # need:
        self.assertTrue(Article.objects.filter(id=a.id).exists())
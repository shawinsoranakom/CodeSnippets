def test_none(self):
        # none() returns a QuerySet that behaves like any other QuerySet object
        self.assertSequenceEqual(Article.objects.none(), [])
        self.assertSequenceEqual(
            Article.objects.none().filter(headline__startswith="Article"), []
        )
        self.assertSequenceEqual(
            Article.objects.filter(headline__startswith="Article").none(), []
        )
        self.assertEqual(Article.objects.none().count(), 0)
        self.assertEqual(
            Article.objects.none().update(headline="This should not take effect"), 0
        )
        self.assertSequenceEqual(list(Article.objects.none().iterator()), [])
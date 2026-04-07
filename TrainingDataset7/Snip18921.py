def test_emptyqs_distinct(self):
        # Tests for #19426
        Article.objects.create(headline="foo", pub_date=datetime.now())
        with self.assertNumQueries(0):
            self.assertEqual(
                len(Article.objects.none().distinct("headline", "pub_date")), 0
            )
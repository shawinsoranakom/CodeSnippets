def test_emptyqs_values(self):
        # test for #15959
        Article.objects.create(headline="foo", pub_date=datetime.now())
        with self.assertNumQueries(0):
            qs = Article.objects.none().values_list("pk")
            self.assertIsInstance(qs, EmptyQuerySet)
            self.assertEqual(len(qs), 0)
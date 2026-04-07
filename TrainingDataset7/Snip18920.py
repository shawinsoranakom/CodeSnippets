def test_emptyqs_values_order(self):
        # Tests for ticket #17712
        Article.objects.create(headline="foo", pub_date=datetime.now())
        with self.assertNumQueries(0):
            self.assertEqual(
                len(Article.objects.none().values_list("id").order_by("id")), 0
            )
        with self.assertNumQueries(0):
            self.assertEqual(
                len(
                    Article.objects.none().filter(
                        id__in=Article.objects.values_list("id", flat=True)
                    )
                ),
                0,
            )
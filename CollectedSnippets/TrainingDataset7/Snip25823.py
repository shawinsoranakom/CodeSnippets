def test_in_different_database(self):
        with self.assertRaisesMessage(
            ValueError,
            "Subqueries aren't allowed across different databases. Force the "
            "inner query to be evaluated using `list(inner_query)`.",
        ):
            list(Article.objects.filter(id__in=Article.objects.using("other").all()))
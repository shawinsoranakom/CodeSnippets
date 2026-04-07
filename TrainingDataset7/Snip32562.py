def test_queries_on_textfields(self):
        """
        Regression tests for #5087

        make sure we can perform queries on TextFields.
        """

        a = Article(name="Test", text="The quick brown fox jumps over the lazy dog.")
        a.save()
        self.assertEqual(
            Article.objects.get(
                text__exact="The quick brown fox jumps over the lazy dog."
            ),
            a,
        )

        self.assertEqual(Article.objects.get(text__contains="quick brown fox"), a)
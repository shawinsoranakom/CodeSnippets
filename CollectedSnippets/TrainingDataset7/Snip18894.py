def test_for_datetimefields_saves_as_much_precision_as_was_given(self):
        """as much precision in *seconds*"""
        a1 = Article(
            headline="Article 7",
            pub_date=datetime(2005, 7, 31, 12, 30),
        )
        a1.save()
        self.assertEqual(
            Article.objects.get(id__exact=a1.id).pub_date, datetime(2005, 7, 31, 12, 30)
        )

        a2 = Article(
            headline="Article 8",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a2.save()
        self.assertEqual(
            Article.objects.get(id__exact=a2.id).pub_date,
            datetime(2005, 7, 31, 12, 30, 45),
        )
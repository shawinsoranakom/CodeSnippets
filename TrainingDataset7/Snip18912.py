def test_unicode_data(self):
        # Unicode data works, too.
        a = Article(
            headline="\u6797\u539f \u3081\u3050\u307f",
            pub_date=datetime(2005, 7, 28),
        )
        a.save()
        self.assertEqual(
            Article.objects.get(pk=a.id).headline, "\u6797\u539f \u3081\u3050\u307f"
        )
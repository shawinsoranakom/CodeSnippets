def test_timezones(self):
        # Saving and updating with timezone-aware datetime Python objects.
        # Regression test for #10443.
        # The idea is that all these creations and saving should work without
        # crashing. It's not rocket science.
        dt1 = datetime.datetime(2008, 8, 31, 16, 20, tzinfo=get_fixed_timezone(600))
        dt2 = datetime.datetime(2008, 8, 31, 17, 20, tzinfo=get_fixed_timezone(600))
        obj = Article.objects.create(
            headline="A headline", pub_date=dt1, article_text="foo"
        )
        obj.pub_date = dt2
        obj.save()
        self.assertEqual(
            Article.objects.filter(headline="A headline").update(pub_date=dt1), 1
        )
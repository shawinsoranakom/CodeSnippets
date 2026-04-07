def test_datetimes_disallows_date_fields(self):
        dt = datetime.datetime(2005, 7, 28, 12, 15)
        Article.objects.create(
            pub_date=dt,
            published_on=dt.date(),
            title="Don't put dates into datetime functions!",
        )
        with self.assertRaisesMessage(
            ValueError, "Cannot truncate DateField 'published_on' to DateTimeField"
        ):
            list(Article.objects.datetimes("published_on", "second"))
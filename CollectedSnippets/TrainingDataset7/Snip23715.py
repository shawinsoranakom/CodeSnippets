def test_aware_datetime_year_view(self):
        BookSigning.objects.create(
            event_date=datetime.datetime(2008, 4, 2, 12, 0, tzinfo=datetime.UTC)
        )
        res = self.client.get("/dates/booksignings/2008/")
        self.assertEqual(res.status_code, 200)
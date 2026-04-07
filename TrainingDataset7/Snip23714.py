def test_datetime_year_view(self):
        BookSigning.objects.create(event_date=datetime.datetime(2008, 4, 2, 12, 0))
        res = self.client.get("/dates/booksignings/2008/")
        self.assertEqual(res.status_code, 200)
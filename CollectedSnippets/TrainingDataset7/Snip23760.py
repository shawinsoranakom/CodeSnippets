def test_datetime_date_detail(self):
        bs = BookSigning.objects.create(event_date=datetime.datetime(2008, 4, 2, 12, 0))
        res = self.client.get("/dates/booksignings/2008/apr/2/%s/" % bs.pk)
        self.assertEqual(res.status_code, 200)
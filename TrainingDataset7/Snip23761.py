def test_aware_datetime_date_detail(self):
        bs = BookSigning.objects.create(
            event_date=datetime.datetime(2008, 4, 2, 12, 0, tzinfo=datetime.UTC)
        )
        res = self.client.get("/dates/booksignings/2008/apr/2/%s/" % bs.pk)
        self.assertEqual(res.status_code, 200)
        # 2008-04-02T00:00:00+03:00 (beginning of day) >
        # 2008-04-01T22:00:00+00:00 (book signing event date).
        bs.event_date = datetime.datetime(2008, 4, 1, 22, 0, tzinfo=datetime.UTC)
        bs.save()
        res = self.client.get("/dates/booksignings/2008/apr/2/%s/" % bs.pk)
        self.assertEqual(res.status_code, 200)
        # 2008-04-03T00:00:00+03:00 (end of day) > 2008-04-02T22:00:00+00:00
        # (book signing event date).
        bs.event_date = datetime.datetime(2008, 4, 2, 22, 0, tzinfo=datetime.UTC)
        bs.save()
        res = self.client.get("/dates/booksignings/2008/apr/2/%s/" % bs.pk)
        self.assertEqual(res.status_code, 404)
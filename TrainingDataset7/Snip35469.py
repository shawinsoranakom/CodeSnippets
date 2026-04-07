def test_query_filter_with_naive_datetime(self):
        dt = datetime.datetime(2011, 9, 1, 12, 20, 30, tzinfo=EAT)
        Event.objects.create(dt=dt)
        dt = dt.replace(tzinfo=None)
        # naive datetimes are interpreted in local time
        with self.assertWarnsMessage(RuntimeWarning, self.naive_warning):
            self.assertEqual(Event.objects.filter(dt__exact=dt).count(), 1)
        with self.assertWarnsMessage(RuntimeWarning, self.naive_warning):
            self.assertEqual(Event.objects.filter(dt__lte=dt).count(), 1)
        with self.assertWarnsMessage(RuntimeWarning, self.naive_warning):
            self.assertEqual(Event.objects.filter(dt__gt=dt).count(), 0)
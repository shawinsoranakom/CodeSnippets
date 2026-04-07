def test_query_filter(self):
        dt1 = datetime.datetime(2011, 9, 1, 12, 20, 30)
        dt2 = datetime.datetime(2011, 9, 1, 14, 20, 30)
        Event.objects.create(dt=dt1)
        Event.objects.create(dt=dt2)
        self.assertEqual(Event.objects.filter(dt__gte=dt1).count(), 2)
        self.assertEqual(Event.objects.filter(dt__gt=dt1).count(), 1)
        self.assertEqual(Event.objects.filter(dt__gte=dt2).count(), 1)
        self.assertEqual(Event.objects.filter(dt__gt=dt2).count(), 0)
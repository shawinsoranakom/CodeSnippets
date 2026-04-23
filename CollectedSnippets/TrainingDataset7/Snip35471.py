def test_query_datetime_lookups_in_other_timezone(self):
        Event.objects.create(dt=datetime.datetime(2011, 1, 1, 1, 30, 0, tzinfo=EAT))
        Event.objects.create(dt=datetime.datetime(2011, 1, 1, 4, 30, 0, tzinfo=EAT))
        with timezone.override(UTC):
            # These two dates fall in the same day in EAT, but in different
            # days, years and months in UTC.
            self.assertEqual(Event.objects.filter(dt__year=2011).count(), 1)
            self.assertEqual(Event.objects.filter(dt__month=1).count(), 1)
            self.assertEqual(Event.objects.filter(dt__day=1).count(), 1)
            self.assertEqual(Event.objects.filter(dt__week_day=7).count(), 1)
            self.assertEqual(Event.objects.filter(dt__iso_week_day=6).count(), 1)
            self.assertEqual(Event.objects.filter(dt__hour=22).count(), 1)
            self.assertEqual(Event.objects.filter(dt__minute=30).count(), 2)
            self.assertEqual(Event.objects.filter(dt__second=0).count(), 2)
def test_filter_date_field_with_aware_datetime(self):
        # Regression test for #17742
        day = datetime.date(2011, 9, 1)
        AllDayEvent.objects.create(day=day)
        # This is 2011-09-02T01:30:00+03:00 in EAT
        dt = datetime.datetime(2011, 9, 1, 22, 30, 0, tzinfo=UTC)
        self.assertFalse(AllDayEvent.objects.filter(day__gte=dt).exists())
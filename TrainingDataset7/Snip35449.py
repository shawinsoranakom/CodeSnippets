def test_query_aggregation(self):
        # Only min and max make sense for datetimes.
        Event.objects.create(dt=datetime.datetime(2011, 9, 1, 23, 20, 20))
        Event.objects.create(dt=datetime.datetime(2011, 9, 1, 13, 20, 30))
        Event.objects.create(dt=datetime.datetime(2011, 9, 1, 3, 20, 40))
        result = Event.objects.aggregate(Min("dt"), Max("dt"))
        self.assertEqual(
            result,
            {
                "dt__min": datetime.datetime(2011, 9, 1, 3, 20, 40),
                "dt__max": datetime.datetime(2011, 9, 1, 23, 20, 20),
            },
        )
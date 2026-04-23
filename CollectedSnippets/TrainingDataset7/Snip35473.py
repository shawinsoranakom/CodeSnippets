def test_query_annotation(self):
        # Only min and max make sense for datetimes.
        morning = Session.objects.create(name="morning")
        afternoon = Session.objects.create(name="afternoon")
        SessionEvent.objects.create(
            dt=datetime.datetime(2011, 9, 1, 23, 20, 20, tzinfo=EAT), session=afternoon
        )
        SessionEvent.objects.create(
            dt=datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT), session=afternoon
        )
        SessionEvent.objects.create(
            dt=datetime.datetime(2011, 9, 1, 3, 20, 40, tzinfo=EAT), session=morning
        )
        morning_min_dt = datetime.datetime(2011, 9, 1, 3, 20, 40, tzinfo=EAT)
        afternoon_min_dt = datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT)
        self.assertQuerySetEqual(
            Session.objects.annotate(dt=Min("events__dt")).order_by("dt"),
            [morning_min_dt, afternoon_min_dt],
            transform=lambda d: d.dt,
        )
        self.assertQuerySetEqual(
            Session.objects.annotate(dt=Min("events__dt")).filter(
                dt__lt=afternoon_min_dt
            ),
            [morning_min_dt],
            transform=lambda d: d.dt,
        )
        self.assertQuerySetEqual(
            Session.objects.annotate(dt=Min("events__dt")).filter(
                dt__gte=afternoon_min_dt
            ),
            [afternoon_min_dt],
            transform=lambda d: d.dt,
        )
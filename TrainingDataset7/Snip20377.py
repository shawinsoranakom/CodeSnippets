def test_extract_func(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 10, 50, 123)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        with self.assertRaisesMessage(ValueError, "lookup_name must be provided"):
            Extract("start_datetime")

        msg = (
            "Extract input expression must be DateField, DateTimeField, TimeField, or "
            "DurationField."
        )
        with self.assertRaisesMessage(ValueError, msg):
            list(DTModel.objects.annotate(extracted=Extract("name", "hour")))

        with self.assertRaisesMessage(
            ValueError,
            "Cannot extract time component 'second' from DateField 'start_date'.",
        ):
            list(DTModel.objects.annotate(extracted=Extract("start_date", "second")))

        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "year")
            ).order_by("start_datetime"),
            [(start_datetime, start_datetime.year), (end_datetime, end_datetime.year)],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "quarter")
            ).order_by("start_datetime"),
            [(start_datetime, 2), (end_datetime, 2)],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "month")
            ).order_by("start_datetime"),
            [
                (start_datetime, start_datetime.month),
                (end_datetime, end_datetime.month),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "day")
            ).order_by("start_datetime"),
            [(start_datetime, start_datetime.day), (end_datetime, end_datetime.day)],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "week")
            ).order_by("start_datetime"),
            [(start_datetime, 25), (end_datetime, 24)],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "week_day")
            ).order_by("start_datetime"),
            [
                (start_datetime, (start_datetime.isoweekday() % 7) + 1),
                (end_datetime, (end_datetime.isoweekday() % 7) + 1),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "iso_week_day"),
            ).order_by("start_datetime"),
            [
                (start_datetime, start_datetime.isoweekday()),
                (end_datetime, end_datetime.isoweekday()),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "hour")
            ).order_by("start_datetime"),
            [(start_datetime, start_datetime.hour), (end_datetime, end_datetime.hour)],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "minute")
            ).order_by("start_datetime"),
            [
                (start_datetime, start_datetime.minute),
                (end_datetime, end_datetime.minute),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                extracted=Extract("start_datetime", "second")
            ).order_by("start_datetime"),
            [
                (start_datetime, start_datetime.second),
                (end_datetime, end_datetime.second),
            ],
            lambda m: (m.start_datetime, m.extracted),
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_datetime__year=Extract("start_datetime", "year")
            ).count(),
            2,
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_datetime__hour=Extract("start_datetime", "hour")
            ).count(),
            2,
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_date__month=Extract("start_date", "month")
            ).count(),
            2,
        )
        self.assertEqual(
            DTModel.objects.filter(
                start_time__hour=Extract("start_time", "hour")
            ).count(),
            2,
        )
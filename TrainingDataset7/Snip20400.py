def _test_trunc_week(self, start_datetime, end_datetime):
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.create_model(end_datetime, start_datetime)

        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                truncated=Trunc("start_datetime", "week", output_field=DateTimeField())
            ).order_by("start_datetime"),
            [
                (start_datetime, truncate_to(start_datetime, "week")),
                (end_datetime, truncate_to(end_datetime, "week")),
            ],
            lambda m: (m.start_datetime, m.truncated),
        )
        self.assertQuerySetEqual(
            DTModel.objects.annotate(
                truncated=Trunc("start_date", "week", output_field=DateField())
            ).order_by("start_datetime"),
            [
                (start_datetime, truncate_to(start_datetime.date(), "week")),
                (end_datetime, truncate_to(end_datetime.date(), "week")),
            ],
            lambda m: (m.start_datetime, m.truncated),
        )
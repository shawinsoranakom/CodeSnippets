def test_trunc_time_comparison(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 26)  # 0 microseconds.
        end_datetime = datetime.datetime(2015, 6, 15, 14, 30, 26, 321)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        self.assertIs(
            DTModel.objects.filter(
                start_datetime__time=start_datetime.time(),
                end_datetime__time=end_datetime.time(),
            ).exists(),
            True,
        )
        self.assertIs(
            DTModel.objects.annotate(
                extracted_start=TruncTime("start_datetime"),
                extracted_end=TruncTime("end_datetime"),
            )
            .filter(
                extracted_start=start_datetime.time(),
                extracted_end=end_datetime.time(),
            )
            .exists(),
            True,
        )
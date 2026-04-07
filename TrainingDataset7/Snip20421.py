def test_extract_func_with_timezone_minus_no_offset(self):
        start_datetime = datetime.datetime(2015, 6, 15, 23, 30, 1, 321)
        end_datetime = datetime.datetime(2015, 6, 16, 13, 11, 27, 123)
        start_datetime = timezone.make_aware(start_datetime)
        end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        ust_nera = zoneinfo.ZoneInfo("Asia/Ust-Nera")

        qs = DTModel.objects.annotate(
            hour=ExtractHour("start_datetime"),
            hour_tz=ExtractHour("start_datetime", tzinfo=ust_nera),
        ).order_by("start_datetime")

        utc_model = qs.get()
        self.assertEqual(utc_model.hour, 23)
        self.assertEqual(utc_model.hour_tz, 9)

        with timezone.override(ust_nera):
            ust_nera_model = qs.get()

        self.assertEqual(ust_nera_model.hour, 9)
        self.assertEqual(ust_nera_model.hour_tz, 9)
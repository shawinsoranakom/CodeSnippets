def test_extract_func_with_timezone(self):
        start_datetime = datetime.datetime(2015, 6, 15, 23, 30, 1, 321)
        end_datetime = datetime.datetime(2015, 6, 16, 13, 11, 27, 123)
        start_datetime = timezone.make_aware(start_datetime)
        end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        delta_tzinfo_pos = datetime.timezone(datetime.timedelta(hours=5))
        delta_tzinfo_neg = datetime.timezone(datetime.timedelta(hours=-5, minutes=17))
        melb = zoneinfo.ZoneInfo("Australia/Melbourne")

        qs = DTModel.objects.annotate(
            day=Extract("start_datetime", "day"),
            day_melb=Extract("start_datetime", "day", tzinfo=melb),
            week=Extract("start_datetime", "week", tzinfo=melb),
            isoyear=ExtractIsoYear("start_datetime", tzinfo=melb),
            weekday=ExtractWeekDay("start_datetime"),
            weekday_melb=ExtractWeekDay("start_datetime", tzinfo=melb),
            isoweekday=ExtractIsoWeekDay("start_datetime"),
            isoweekday_melb=ExtractIsoWeekDay("start_datetime", tzinfo=melb),
            quarter=ExtractQuarter("start_datetime", tzinfo=melb),
            hour=ExtractHour("start_datetime"),
            hour_melb=ExtractHour("start_datetime", tzinfo=melb),
            hour_with_delta_pos=ExtractHour("start_datetime", tzinfo=delta_tzinfo_pos),
            hour_with_delta_neg=ExtractHour("start_datetime", tzinfo=delta_tzinfo_neg),
            minute_with_delta_neg=ExtractMinute(
                "start_datetime", tzinfo=delta_tzinfo_neg
            ),
        ).order_by("start_datetime")

        utc_model = qs.get()
        self.assertEqual(utc_model.day, 15)
        self.assertEqual(utc_model.day_melb, 16)
        self.assertEqual(utc_model.week, 25)
        self.assertEqual(utc_model.isoyear, 2015)
        self.assertEqual(utc_model.weekday, 2)
        self.assertEqual(utc_model.weekday_melb, 3)
        self.assertEqual(utc_model.isoweekday, 1)
        self.assertEqual(utc_model.isoweekday_melb, 2)
        self.assertEqual(utc_model.quarter, 2)
        self.assertEqual(utc_model.hour, 23)
        self.assertEqual(utc_model.hour_melb, 9)
        self.assertEqual(utc_model.hour_with_delta_pos, 4)
        self.assertEqual(utc_model.hour_with_delta_neg, 18)
        self.assertEqual(utc_model.minute_with_delta_neg, 47)

        with timezone.override(melb):
            melb_model = qs.get()

        self.assertEqual(melb_model.day, 16)
        self.assertEqual(melb_model.day_melb, 16)
        self.assertEqual(melb_model.week, 25)
        self.assertEqual(melb_model.isoyear, 2015)
        self.assertEqual(melb_model.weekday, 3)
        self.assertEqual(melb_model.isoweekday, 2)
        self.assertEqual(melb_model.quarter, 2)
        self.assertEqual(melb_model.weekday_melb, 3)
        self.assertEqual(melb_model.isoweekday_melb, 2)
        self.assertEqual(melb_model.hour, 9)
        self.assertEqual(melb_model.hour_melb, 9)
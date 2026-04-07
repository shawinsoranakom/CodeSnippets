def test_extract_func_explicit_timezone_priority(self):
        start_datetime = datetime.datetime(2015, 6, 15, 23, 30, 1, 321)
        end_datetime = datetime.datetime(2015, 6, 16, 13, 11, 27, 123)
        start_datetime = timezone.make_aware(start_datetime)
        end_datetime = timezone.make_aware(end_datetime)
        self.create_model(start_datetime, end_datetime)
        melb = zoneinfo.ZoneInfo("Australia/Melbourne")
        with timezone.override(melb):
            model = (
                DTModel.objects.annotate(
                    day_melb=Extract("start_datetime", "day"),
                    day_utc=Extract("start_datetime", "day", tzinfo=datetime.UTC),
                )
                .order_by("start_datetime")
                .get()
            )
            self.assertEqual(model.day_melb, 16)
            self.assertEqual(model.day_utc, 15)
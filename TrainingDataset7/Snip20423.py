def test_extract_invalid_field_with_timezone(self):
        melb = zoneinfo.ZoneInfo("Australia/Melbourne")
        msg = "tzinfo can only be used with DateTimeField."
        with self.assertRaisesMessage(ValueError, msg):
            DTModel.objects.annotate(
                day_melb=Extract("start_date", "day", tzinfo=melb),
            ).get()
        with self.assertRaisesMessage(ValueError, msg):
            DTModel.objects.annotate(
                hour_melb=Extract("start_time", "hour", tzinfo=melb),
            ).get()